from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.clinics.models import Clinic
from apps.dental_cases.models import DentalCase
from apps.dental_cases.services import DentalCaseService
from apps.laboratories.models import Laboratory
from apps.users.services import LaboratoryUserService
from apps.workflow.models import Workflow

from .permissions import (
    Operation,
    Role,
    can,
    can_in,
    get_role,
    is_blocked,
)
from .screens import build_menu

TODAS_LAS_OPERACIONES = {
    Operation.CREATE_CASES,
    Operation.VIEW_CASES,
    Operation.MANAGE_CASES,
    Operation.UPDATE_PRODUCTION,
    Operation.MANAGE_INVENTORY,
    Operation.VIEW_REPORTS,
    Operation.CONFIGURE_LABORATORY,
    Operation.MANAGE_USERS,
}


def build_laboratory(name, email):
    """
    Creates a laboratory with sensible defaults for the tests.
    """

    return Laboratory.objects.create(
        name=name,
        email=email,
        phone="1",
        city="Medellin",
        address="Calle 1",
        service="CROWN",
    )


def build_member(username, laboratory, role, status="ACTIVE"):
    """
    Registers a laboratory user the way the application does and
    returns the account they sign in with.
    """

    member = LaboratoryUserService.register(
        {
            "username": username,
            "password": "Clave-de-prueba-2026",
            "email": f"{username}@test.com",
            "first_name": username.capitalize(),
            "last_name": "Prueba",
            "role": role,
            "status": status,
        },
        laboratory,
    )

    return member.user


def build_case(case_number, **overrides):
    """
    Creates a dental case with sensible defaults for the tests.
    """

    data = {
        "clinic_name": "Clinica Prueba",
        "requested_by": "Dra. Prueba",
        "service_type": "CROWN",
        "description": "Caso de prueba",
        "status": DentalCase.Status.SUBMITTED,
        "due_date": timezone.now().date() + timedelta(days=7),
    }

    data.update(overrides)

    return DentalCase.objects.create(case_number=case_number, **data)


def build_clinic(name, nit):
    """
    Creates a dental clinic with sensible defaults for the tests.
    """

    return Clinic.objects.create(
        name=name,
        nit=nit,
        email=f"{nit}@clinica.com",
        phone="1",
        address="Calle 2",
        city="Medellin",
        contact_person="Contacto",
    )


def build_clinic_user(username, clinic):
    """
    Creates an account that belongs to a clinic.
    """

    user = User.objects.create_user(username, password="clave")
    clinic.users.add(user)

    return user


class RoleMatrixTests(TestCase):
    """
    Que operaciones permite cada rol.
    """

    def setUp(self):

        self.propio = build_laboratory("Lab Propio", "propio@test.com")
        self.ajeno = build_laboratory("Lab Ajeno", "ajeno@test.com")

    def assert_operations(self, user, laboratory, expected):
        for operation in TODAS_LAS_OPERACIONES:
            with self.subTest(operation=operation):
                self.assertEqual(
                    can_in(user, operation, laboratory),
                    operation in expected,
                )

    def test_administrator_can_do_everything_in_the_laboratory(self):

        admin = build_member("admin_lab", self.propio, Role.ADMIN)

        self.assert_operations(admin, self.propio, TODAS_LAS_OPERACIONES)

    def test_receptionist_receives_views_and_manages_cases(self):

        recepcion = build_member("recepcion", self.propio, Role.RECEPTIONIST)

        self.assert_operations(
            recepcion,
            self.propio,
            {
                Operation.CREATE_CASES,
                Operation.VIEW_CASES,
                Operation.MANAGE_CASES,
            },
        )

    def test_technician_works_on_production_and_inventory(self):

        tecnico = build_member("tecnico", self.propio, Role.TECHNICIAN)

        self.assert_operations(
            tecnico,
            self.propio,
            {
                Operation.VIEW_CASES,
                Operation.UPDATE_PRODUCTION,
                Operation.MANAGE_INVENTORY,
            },
        )

    def test_role_does_not_reach_another_laboratory(self):
        """
        Ser administrador de un laboratorio no da nada en otro.
        """

        admin = build_member("admin_lab", self.propio, Role.ADMIN)

        self.assert_operations(admin, self.ajeno, set())

    def test_inactive_user_has_no_role(self):
        """
        Un usuario inactivo conserva la cuenta pero no puede hacer nada.
        """

        inactivo = build_member(
            "inactivo", self.propio, Role.ADMIN, status="INACTIVE"
        )

        self.assertTrue(is_blocked(inactivo))
        self.assertIsNone(get_role(inactivo, self.propio))
        self.assert_operations(inactivo, self.propio, set())

    def test_account_without_laboratory_has_no_role(self):
        """
        Una cuenta de clinica no tiene rol en ningun laboratorio.
        """

        clinica = User.objects.create_user("clinica", password="clave")

        self.assertFalse(is_blocked(clinica))
        self.assertIsNone(get_role(clinica, self.propio))
        self.assertFalse(can(clinica, Operation.VIEW_REPORTS))

    def test_superuser_can_do_everything(self):

        superusuario = User.objects.create_superuser(
            "root", password="clave", email="root@test.com"
        )

        self.assert_operations(
            superusuario, self.ajeno, TODAS_LAS_OPERACIONES
        )

    def test_accounts_from_before_roles_keep_their_access(self):
        """
        Las cuentas anteriores a los roles no tienen membresia: las
        listas del laboratorio les dan el rol que ya ejercian.
        """

        autorizado = User.objects.create_user("autorizado", password="clave")
        self.propio.authorized_users.add(autorizado)

        operario = User.objects.create_user("operario", password="clave")
        self.propio.technicians.add(operario)

        self.assertEqual(get_role(autorizado, self.propio), Role.ADMIN)
        self.assertEqual(get_role(operario, self.propio), Role.TECHNICIAN)

    def test_membership_wins_over_the_laboratory_lists(self):
        """
        Registrar a alguien lo agrega a las listas del laboratorio,
        pero el rol que vale es el de su membresia.
        """

        tecnico = build_member("tecnico", self.propio, Role.TECHNICIAN)

        self.assertTrue(
            self.propio.authorized_users.filter(pk=tecnico.pk).exists()
        )
        self.assertEqual(get_role(tecnico, self.propio), Role.TECHNICIAN)


class SessionRequiredTests(TestCase):
    """
    Ninguna pantalla funciona sin iniciar sesion.
    """

    def setUp(self):

        laboratory = build_laboratory("Lab Propio", "propio@test.com")

        clinic = Clinic.objects.create(
            name="Clinica Sonrisa",
            nit="900123456",
            email="clinica@test.com",
            phone="1",
            address="Calle 2",
            city="Medellin",
            contact_person="Dra. Prueba",
        )

        case = build_case("S-001", laboratory=laboratory)

        self.urls = [
            reverse("dashboard"),
            reverse("dental_case_list"),
            reverse("dental_case_create"),
            reverse("dental_case_detail", args=[case.id]),
            reverse("dental_case_edit", args=[case.id]),
            reverse("dental_case_delete", args=[case.id]),
            reverse("dental_case_reject", args=[case.id]),
            reverse("technician_assignment", args=[case.id]),
            reverse("laboratory_case_inbox", args=[laboratory.id]),
            reverse("clinic_case_inbox", args=[clinic.id]),
            reverse("case_tracking", args=[case.id]),
            reverse("workflow_list"),
            reverse("workflow_create"),
            reverse("clinic_list"),
            reverse("clinic_create"),
            reverse("laboratory_list"),
            reverse("laboratory_create"),
            reverse("technician_create", args=[laboratory.id]),
            reverse("material_list"),
            reverse("operational_reports"),
            reverse("users:create"),
        ]

        self.accept_url = reverse("dental_case_accept", args=[case.id])
        self.case = case

    def test_anonymous_user_is_sent_to_the_login(self):

        login_url = reverse("login")

        for url in self.urls:
            with self.subTest(url=url):

                response = self.client.get(url)

                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith(login_url))

    def test_anonymous_user_cannot_accept_a_case(self):
        """
        Antes de FR-16 esto funcionaba sin tener cuenta.
        """

        response = self.client.post(self.accept_url)

        self.case.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.case.acceptance_status,
            DentalCase.AcceptanceStatus.PENDING,
        )


class ScreenAccessTests(TestCase):
    """
    Cada pantalla verifica el rol antes de ejecutarse.
    """

    def setUp(self):

        self.propio = build_laboratory("Lab Propio", "propio@test.com")
        self.ajeno = build_laboratory("Lab Ajeno", "ajeno@test.com")

        self.cuentas = {
            "admin": build_member("admin_lab", self.propio, Role.ADMIN),
            "recepcion": build_member(
                "recepcion", self.propio, Role.RECEPTIONIST
            ),
            "tecnico": build_member("tecnico", self.propio, Role.TECHNICIAN),
            "clinica": User.objects.create_user("clinica", password="clave"),
        }

        self.pantallas = {
            "bandeja": reverse("laboratory_case_inbox", args=[self.propio.id]),
            "workflow": reverse("workflow_list"),
            "inventario": reverse("material_list"),
            "reportes": reverse("operational_reports"),
            "etapas": reverse("workflow_stage_list", args=[self.propio.id]),
            "usuarios": reverse("users:create"),
        }

    def assert_access(self, cuenta, permitidas):

        self.client.force_login(self.cuentas[cuenta])

        for nombre, url in self.pantallas.items():
            with self.subTest(cuenta=cuenta, pantalla=nombre):
                self.assertEqual(
                    self.client.get(url).status_code,
                    200 if nombre in permitidas else 403,
                )

    def test_administrator_opens_every_screen(self):

        self.assert_access("admin", set(self.pantallas))

    def test_receptionist_screens(self):

        self.assert_access("recepcion", {"bandeja", "workflow"})

    def test_technician_screens(self):

        self.assert_access("tecnico", {"bandeja", "workflow", "inventario"})

    def test_clinic_account_opens_no_laboratory_screen(self):

        self.assert_access("clinica", set())

    def test_administrator_cannot_open_another_laboratory(self):

        self.client.force_login(self.cuentas["admin"])

        for screen in ("laboratory_case_inbox", "workflow_stage_list"):
            with self.subTest(screen=screen):

                response = self.client.get(
                    reverse(screen, args=[self.ajeno.id])
                )

                self.assertEqual(response.status_code, 403)

    def test_denied_screen_explains_the_reason(self):

        self.client.force_login(self.cuentas["tecnico"])

        response = self.client.get(self.pantallas["reportes"])

        self.assertContains(
            response,
            "Your role does not allow this operation.",
            status_code=403,
        )

    def test_inactive_user_is_blocked_everywhere(self):
        """
        Un usuario inactivo entra, pero ninguna pantalla lo deja pasar.
        """

        inactivo = build_member(
            "inactivo", self.propio, Role.ADMIN, status="INACTIVE"
        )

        self.client.force_login(inactivo)

        for url in (reverse("dashboard"), reverse("dental_case_list")):
            with self.subTest(url=url):
                self.assertContains(
                    self.client.get(url),
                    "Your laboratory account is inactive.",
                    status_code=403,
                )

    def test_inactive_user_can_still_sign_out(self):

        inactivo = build_member(
            "inactivo", self.propio, Role.ADMIN, status="INACTIVE"
        )

        self.client.force_login(inactivo)

        response = self.client.post(reverse("logout"))

        self.assertEqual(response.status_code, 302)


class CaseOperationTests(TestCase):
    """
    Las acciones sobre un caso verifican el rol en su laboratorio.
    """

    def setUp(self):

        self.laboratory = build_laboratory("Lab Propio", "propio@test.com")

        self.admin = build_member("admin_lab", self.laboratory, Role.ADMIN)
        self.recepcion = build_member(
            "recepcion", self.laboratory, Role.RECEPTIONIST
        )
        self.tecnico = build_member(
            "tecnico", self.laboratory, Role.TECHNICIAN
        )
        self.clinica = User.objects.create_user("clinica", password="clave")
        self.ajeno = User.objects.create_user("ajeno", password="clave")

        self.case = build_case(
            "C-001",
            laboratory=self.laboratory,
            created_by=self.clinica,
        )

        self.detail_url = reverse("dental_case_detail", args=[self.case.id])
        self.accept_url = reverse("dental_case_accept", args=[self.case.id])

    def start_production(self):
        """
        Leaves the case in production, with its workflow created.
        """

        DentalCaseService.accept(self.case)
        DentalCaseService.assign_technician(self.case, self.tecnico)

        self.client.force_login(self.recepcion)
        self.client.post(reverse("start_production", args=[self.case.id]))

        return Workflow.objects.get(dental_case=self.case)

    def test_receptionist_accepts_a_case(self):

        self.client.force_login(self.recepcion)

        self.client.post(self.accept_url)
        self.case.refresh_from_db()

        self.assertEqual(
            self.case.acceptance_status,
            DentalCase.AcceptanceStatus.ACCEPTED,
        )

    def test_technician_and_clinic_cannot_accept_a_case(self):

        for cuenta in (self.tecnico, self.clinica):
            with self.subTest(cuenta=cuenta.username):

                self.client.force_login(cuenta)

                response = self.client.post(self.accept_url)
                self.case.refresh_from_db()

                self.assertEqual(response.status_code, 403)
                self.assertEqual(
                    self.case.acceptance_status,
                    DentalCase.AcceptanceStatus.PENDING,
                )

    def test_case_detail_is_only_for_those_related_to_the_case(self):

        for cuenta, esperado in (
            (self.clinica, 200),
            (self.recepcion, 200),
            (self.tecnico, 200),
            (self.ajeno, 403),
        ):
            with self.subTest(cuenta=cuenta.username):

                self.client.force_login(cuenta)

                self.assertEqual(
                    self.client.get(self.detail_url).status_code,
                    esperado,
                )

    def test_management_buttons_depend_on_the_role(self):
        """
        Los botones de gestion solo se ofrecen a quien puede usarlos.
        """

        for cuenta, esperado in (
            (self.admin, True),
            (self.recepcion, True),
            (self.tecnico, False),
            (self.clinica, False),
        ):
            with self.subTest(cuenta=cuenta.username):

                self.client.force_login(cuenta)

                response = self.client.get(self.detail_url)

                self.assertEqual(
                    response.context["can_manage_laboratory"],
                    esperado,
                )

    def test_editing_requires_more_than_seeing_the_case(self):
        """
        El tecnico ve el caso pero no puede editarlo ni borrarlo.
        """

        for screen in ("dental_case_edit", "dental_case_delete"):

            url = reverse(screen, args=[self.case.id])

            for cuenta, esperado in (
                (self.clinica, 200),
                (self.recepcion, 200),
                (self.tecnico, 403),
            ):
                with self.subTest(screen=screen, cuenta=cuenta.username):

                    self.client.force_login(cuenta)

                    self.assertEqual(
                        self.client.get(url).status_code,
                        esperado,
                    )

    def test_only_case_managers_start_production(self):

        DentalCaseService.accept(self.case)
        DentalCaseService.assign_technician(self.case, self.tecnico)

        url = reverse("start_production", args=[self.case.id])

        self.client.force_login(self.tecnico)

        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertFalse(Workflow.objects.filter(dental_case=self.case).exists())

        self.client.force_login(self.recepcion)
        self.client.post(url)

        self.assertTrue(Workflow.objects.filter(dental_case=self.case).exists())

    def test_technician_updates_the_production_progress(self):

        workflow = self.start_production()

        url = reverse("workflow_update_stage", args=[workflow.id])

        self.client.force_login(self.tecnico)

        self.client.post(
            url,
            {
                "current_stage": "DESIGN",
                "progress_percentage": 30,
                "comment": "Diseno iniciado",
            },
        )

        workflow.refresh_from_db()

        self.assertEqual(workflow.current_stage, "DESIGN")

    def test_receptionist_cannot_update_the_production_progress(self):

        workflow = self.start_production()

        self.client.force_login(self.recepcion)

        response = self.client.post(
            reverse("workflow_update_stage", args=[workflow.id]),
            {
                "current_stage": "DESIGN",
                "progress_percentage": 30,
                "comment": "",
            },
        )

        workflow.refresh_from_db()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(workflow.current_stage, "RECEIVED")

    def test_tracking_offers_the_update_only_to_production_roles(self):

        self.start_production()

        url = reverse("case_tracking", args=[self.case.id])

        for cuenta, esperado in (
            (self.tecnico, True),
            (self.admin, True),
            (self.recepcion, False),
            (self.clinica, False),
        ):
            with self.subTest(cuenta=cuenta.username):

                self.client.force_login(cuenta)

                response = self.client.get(url)

                self.assertEqual(
                    response.context["can_update_production"],
                    esperado,
                )

    def test_tracking_is_closed_to_unrelated_accounts(self):

        self.client.force_login(self.ajeno)

        response = self.client.get(
            reverse("case_tracking", args=[self.case.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_workflow_list_only_shows_visible_cases(self):

        self.start_production()

        otro_laboratorio = build_laboratory("Lab Ajeno", "ajeno@test.com")
        externo = build_member("externo", otro_laboratorio, Role.ADMIN)

        self.client.force_login(externo)

        response = self.client.get(reverse("workflow_list"))

        self.assertEqual(len(response.context["workflows"]), 0)

        self.client.force_login(self.tecnico)

        response = self.client.get(reverse("workflow_list"))

        self.assertEqual(len(response.context["workflows"]), 1)


class MenuTests(TestCase):
    """
    El menu ofrece a cada rol solo lo que puede abrir.
    """

    def setUp(self):

        self.laboratory = build_laboratory("Lab Propio", "propio@test.com")
        self.clinic = build_clinic("Clinica Sonrisa", "900111")

        self.cuentas = {
            "admin": build_member("admin_lab", self.laboratory, Role.ADMIN),
            "recepcion": build_member(
                "recepcion", self.laboratory, Role.RECEPTIONIST
            ),
            "tecnico": build_member(
                "tecnico", self.laboratory, Role.TECHNICIAN
            ),
            "clinica": build_clinic_user("clinica", self.clinic),
            "particular": User.objects.create_user("particular", password="clave"),
        }

    def labels(self, cuenta):
        """
        Returns every label of the menu, including those of the dropdowns.
        """

        labels = set()

        for item in build_menu(self.cuentas[cuenta]):
            labels.add(item["label"])
            for child in item.get("children", []):
                labels.add(child["label"])

        return labels

    def urls(self, user):
        """
        Returns every address the menu offers to the user.
        """

        urls = []

        for item in build_menu(user):
            if "url" in item:
                urls.append((item["label"], item["url"]))
            for child in item.get("children", []):
                urls.append((child["label"], child["url"]))

        return urls

    def test_menu_of_each_role(self):

        esperado = {
            "admin": {
                "Dashboard", "Cases", "List Cases", "Create Case",
                "Laboratory Inbox", "Clinics", "Labs", "Workflow",
                "Inventory", "Reports", "Laboratory", "Workflow Stages",
                "Register User",
            },
            "recepcion": {
                "Cases", "List Cases", "Create Case", "Laboratory Inbox",
                "Clinics", "Labs", "Workflow",
            },
            "tecnico": {
                "Cases", "List Cases", "Laboratory Inbox", "Clinics",
                "Labs", "Workflow", "Inventory",
            },
            "clinica": {
                "Cases", "List Cases", "Create Case", "My Clinic", "Labs",
            },
            "particular": {"Cases", "List Cases", "Create Case", "Labs"},
        }

        for cuenta, opciones in esperado.items():
            with self.subTest(cuenta=cuenta):
                self.assertEqual(self.labels(cuenta), opciones)

    def test_menu_never_offers_a_screen_that_rejects_the_user(self):
        """
        Todo enlace del menu abre para el usuario que lo ve.
        """

        for cuenta, user in self.cuentas.items():

            self.client.force_login(user)

            for label, url in self.urls(user):
                with self.subTest(cuenta=cuenta, opcion=label):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_menu_marks_the_section_being_shown(self):

        user = self.cuentas["admin"]
        stages = reverse("workflow_stage_list", args=[self.laboratory.id])

        activos = {
            item["label"] for item in build_menu(user, stages) if item["active"]
        }

        self.assertEqual(activos, {"Laboratory"})

    def test_page_shows_the_role_and_its_menu(self):

        self.client.force_login(self.cuentas["tecnico"])

        content = self.client.get(reverse("workflow_list")).content.decode()

        self.assertIn("Technician · Lab Propio", content)
        self.assertIn("Inventory", content)
        self.assertNotIn("Reports", content)
        self.assertNotIn("Register User", content)


class HomePageTests(TestCase):
    """
    Cada rol empieza en su propia pantalla al iniciar sesion.
    """

    def setUp(self):

        self.laboratory = build_laboratory("Lab Propio", "propio@test.com")
        self.clinic = build_clinic("Clinica Sonrisa", "900111")

    def assert_home(self, user, expected):

        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, expected, fetch_redirect_response=False)
        self.assertEqual(self.client.get(expected).status_code, 200)

    def test_administrator_starts_on_the_dashboard(self):

        admin = build_member("admin_lab", self.laboratory, Role.ADMIN)

        self.assert_home(admin, reverse("dashboard"))

    def test_receptionist_starts_on_the_inbox(self):

        recepcion = build_member("recepcion", self.laboratory, Role.RECEPTIONIST)

        self.assert_home(
            recepcion,
            reverse("laboratory_case_inbox", args=[self.laboratory.id]),
        )

    def test_technician_starts_on_the_workflow(self):

        tecnico = build_member("tecnico", self.laboratory, Role.TECHNICIAN)

        self.assert_home(tecnico, reverse("workflow_list"))

    def test_clinic_starts_on_its_own_page(self):

        clinica = build_clinic_user("clinica", self.clinic)

        self.assert_home(clinica, reverse("clinic_detail", args=[self.clinic.id]))

    def test_account_without_role_starts_on_its_cases(self):

        particular = User.objects.create_user("particular", password="clave")

        self.assert_home(particular, reverse("dental_case_list"))

    def test_signing_in_goes_through_the_home_page(self):

        build_member("recepcion", self.laboratory, Role.RECEPTIONIST)

        response = self.client.post(
            reverse("login"),
            {"username": "recepcion", "password": "Clave-de-prueba-2026"},
        )

        self.assertRedirects(
            response, reverse("home"), fetch_redirect_response=False
        )


class ClinicRoleTests(TestCase):
    """
    Las personas de una clinica ven y siguen solo los casos de su clinica.
    """

    def setUp(self):

        self.laboratory = build_laboratory("Lab Propio", "propio@test.com")
        self.clinic = build_clinic("Clinica Sonrisa", "900111")
        self.other_clinic = build_clinic("Clinica Norte", "900222")

        self.clinica = build_clinic_user("clinica", self.clinic)
        self.otra = build_clinic_user("otra", self.other_clinic)

        self.case = build_case(
            "C-001", laboratory=self.laboratory, clinic=self.clinic
        )
        self.other_case = build_case(
            "C-002", laboratory=self.laboratory, clinic=self.other_clinic
        )

    def test_clinic_has_the_clinic_role(self):

        self.assertTrue(can(self.clinica, Operation.CREATE_CASES))
        self.assertFalse(can(self.clinica, Operation.VIEW_CASES))
        self.assertFalse(can(self.clinica, Operation.MANAGE_CASES))

    def test_clinic_sees_only_the_cases_of_its_clinic(self):

        visibles = DentalCaseService.get_visible_cases(self.clinica)

        self.assertEqual(list(visibles), [self.case])

    def test_clinic_follows_its_case_but_not_another(self):

        self.client.force_login(self.clinica)

        own = reverse("dental_case_detail", args=[self.case.id])
        other = reverse("dental_case_detail", args=[self.other_case.id])

        self.assertEqual(self.client.get(own).status_code, 200)
        self.assertEqual(self.client.get(other).status_code, 403)

    def test_clinic_cannot_run_the_laboratory_side_of_its_case(self):

        self.client.force_login(self.clinica)

        response = self.client.post(
            reverse("dental_case_accept", args=[self.case.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_clinic_page_is_only_for_its_people_and_the_laboratories(self):

        page = reverse("clinic_detail", args=[self.clinic.id])

        self.client.force_login(self.otra)
        self.assertEqual(self.client.get(page).status_code, 403)

        tecnico = build_member("tecnico", self.laboratory, Role.TECHNICIAN)
        self.client.force_login(tecnico)
        self.assertEqual(self.client.get(page).status_code, 200)

    def test_clinic_page_lists_only_the_cases_the_user_can_see(self):

        ajeno = build_laboratory("Lab Ajeno", "ajeno@test.com")
        build_case("C-003", laboratory=ajeno, clinic=self.clinic)

        tecnico = build_member("tecnico", self.laboratory, Role.TECHNICIAN)
        self.client.force_login(tecnico)

        response = self.client.get(
            reverse("clinic_detail", args=[self.clinic.id])
        )

        self.assertEqual(
            [case.case_number for case in response.context["cases"]],
            ["C-001"],
        )

    def test_clinic_cannot_open_the_laboratory_screens(self):

        self.client.force_login(self.clinica)

        for url in (
            reverse("dashboard"),
            reverse("clinic_list"),
            reverse("workflow_list"),
            reverse("laboratory_detail", args=[self.laboratory.id]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)


class CaseCreationTests(TestCase):
    """
    Crear un caso es de la clinica y de quien atiende al laboratorio.
    """

    def test_who_may_open_the_case_form(self):

        laboratory = build_laboratory("Lab Propio", "propio@test.com")
        clinic = build_clinic("Clinica Sonrisa", "900111")

        esperado = {
            "admin": (build_member("admin_lab", laboratory, Role.ADMIN), 200),
            "recepcion": (
                build_member("recepcion", laboratory, Role.RECEPTIONIST),
                200,
            ),
            "clinica": (build_clinic_user("clinica", clinic), 200),
            "particular": (
                User.objects.create_user("particular", password="clave"),
                200,
            ),
            "tecnico": (
                build_member("tecnico", laboratory, Role.TECHNICIAN),
                403,
            ),
        }

        for cuenta, (user, status) in esperado.items():
            with self.subTest(cuenta=cuenta):
                self.client.force_login(user)
                self.assertEqual(
                    self.client.get(reverse("dental_case_create")).status_code,
                    status,
                )
