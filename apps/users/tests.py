from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.permissions import Role, get_role
from apps.laboratories.models import Laboratory

from .forms import LaboratoryUserForm
from .models import LaboratoryUser
from .services import LaboratoryUserService

DATOS_VALIDOS = {
    "first_name": "Daniela",
    "last_name": "Restrepo",
    "email": "daniela@laboratorio.com",
    "phone": "+57 300 123 4567",
    "role": "TECHNICIAN",
    "status": "ACTIVE",
}

# Lo que pide la pantalla: los datos de la persona y los de su cuenta.
DATOS_DE_REGISTRO = DATOS_VALIDOS | {
    "username": "daniela",
    "password": "Clave-segura-2026",
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


def build_member(username, laboratory, role):
    """
    Registers a laboratory user and returns the account they sign in with.
    """

    member = LaboratoryUserService.register(
        {
            "username": username,
            "password": "Clave-de-prueba-2026",
            "email": f"{username}@test.com",
            "first_name": username.capitalize(),
            "last_name": "Prueba",
            "role": role,
            "status": "ACTIVE",
        },
        laboratory,
    )

    return member.user


class LaboratoryUserModelTests(TestCase):

    def test_stores_personal_information_role_and_status(self):
        """
        El usuario guarda datos personales, rol y estado.
        """

        usuario = LaboratoryUser.objects.create(**DATOS_VALIDOS)
        usuario.refresh_from_db()

        self.assertEqual(usuario.first_name, "Daniela")
        self.assertEqual(usuario.last_name, "Restrepo")
        self.assertEqual(usuario.email, "daniela@laboratorio.com")
        self.assertEqual(usuario.role, "TECHNICIAN")
        self.assertEqual(usuario.status, "ACTIVE")
        self.assertIsNotNone(usuario.created_at)

    def test_default_role_and_status(self):
        """
        Sin especificar, el usuario nace tecnico y activo.
        """

        datos = {
            k: v
            for k, v in DATOS_VALIDOS.items()
            if k not in ("role", "status")
        }

        usuario = LaboratoryUser.objects.create(**datos)

        self.assertEqual(usuario.role, "TECHNICIAN")
        self.assertEqual(usuario.status, "ACTIVE")


class LaboratoryUserFormTests(TestCase):

    def setUp(self):
        self.laboratory = build_laboratory("Lab Propio", "propio@test.com")

    def form(self, datos):
        return LaboratoryUserForm(datos, laboratory=self.laboratory)

    def test_valid_data_is_accepted(self):
        self.assertTrue(self.form(DATOS_DE_REGISTRO).is_valid())

    def test_invalid_email_is_rejected(self):
        """
        Los datos se validan antes de guardar.
        """

        form = self.form(DATOS_DE_REGISTRO | {"email": "esto-no-es-un-correo"})

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_email_is_rejected(self):
        """
        El correo identifica al usuario, no puede repetirse.
        """

        LaboratoryUser.objects.create(**DATOS_VALIDOS)

        form = self.form(DATOS_DE_REGISTRO)

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_invalid_phone_is_rejected(self):
        """
        El telefono tiene un formato validado.
        """

        form = self.form(DATOS_DE_REGISTRO | {"phone": "no-es-un-telefono"})

        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_required_fields(self):
        """
        Los datos de la persona y los de su cuenta son obligatorios.
        """

        form = self.form({})

        self.assertFalse(form.is_valid())

        for campo in (
            "first_name",
            "last_name",
            "email",
            "username",
            "password",
        ):
            with self.subTest(campo=campo):
                self.assertIn(campo, form.errors)

    def test_duplicate_username_is_rejected(self):

        User.objects.create_user("daniela", password="clave")

        form = self.form(DATOS_DE_REGISTRO)

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_weak_password_is_rejected(self):

        form = self.form(DATOS_DE_REGISTRO | {"password": "123"})

        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_superuser_form_asks_for_the_laboratory(self):
        """
        Sin laboratorio fijo, el formulario exige elegir uno.
        """

        form = LaboratoryUserForm(DATOS_DE_REGISTRO)

        self.assertFalse(form.is_valid())
        self.assertIn("laboratory", form.errors)


class LaboratoryUserViewTests(TestCase):
    """
    El flujo completo de registro desde la interfaz.
    """

    def setUp(self):

        self.url = reverse("users:create")

        self.laboratory = build_laboratory("Lab Propio", "propio@test.com")

        self.admin = build_member("administrador", self.laboratory, Role.ADMIN)

    def test_registration_requires_login(self):
        """
        Un anonimo no puede registrar usuarios del laboratorio.
        """

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            LaboratoryUser.objects.filter(email=DATOS_VALIDOS["email"]).exists()
        )

    def test_only_administrators_register_users(self):
        """
        Registrar usuarios es una operacion del administrador.
        """

        for role in (Role.RECEPTIONIST, Role.TECHNICIAN):
            with self.subTest(role=role):

                cuenta = build_member(
                    f"cuenta_{role.lower()}", self.laboratory, role
                )

                self.client.force_login(cuenta)

                response = self.client.post(self.url, DATOS_DE_REGISTRO)

                self.assertEqual(response.status_code, 403)
                self.assertFalse(
                    User.objects.filter(username="daniela").exists()
                )

    def test_form_page_renders(self):

        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], LaboratoryUserForm)

    def test_registration_saves_the_user(self):
        """
        Registrar desde la interfaz guarda el usuario en la base.
        """

        self.client.force_login(self.admin)

        response = self.client.post(self.url, DATOS_DE_REGISTRO, follow=True)

        self.assertEqual(response.status_code, 200)

        usuario = LaboratoryUser.objects.get(
            email="daniela@laboratorio.com"
        )

        self.assertEqual(usuario.first_name, "Daniela")
        self.assertEqual(usuario.role, "TECHNICIAN")
        self.assertEqual(usuario.status, "ACTIVE")

    def test_registration_links_account_laboratory_and_role(self):
        """
        FR-16: el registro crea la cuenta y la deja enlazada con el
        laboratorio del administrador y con su rol.
        """

        self.client.force_login(self.admin)

        self.client.post(self.url, DATOS_DE_REGISTRO)

        usuario = LaboratoryUser.objects.get(email="daniela@laboratorio.com")
        cuenta = User.objects.get(username="daniela")

        self.assertEqual(usuario.user, cuenta)
        self.assertEqual(usuario.laboratory, self.laboratory)
        self.assertEqual(get_role(cuenta, self.laboratory), Role.TECHNICIAN)

        # Las listas del laboratorio, que la asignacion de tecnicos lee.
        self.assertTrue(
            self.laboratory.technicians.filter(pk=cuenta.pk).exists()
        )

    def test_registered_user_can_sign_in_with_the_role(self):
        """
        La cuenta nueva entra con su clave y ve lo que su rol permite.
        """

        self.client.force_login(self.admin)
        self.client.post(self.url, DATOS_DE_REGISTRO)
        self.client.logout()

        self.assertTrue(
            self.client.login(
                username="daniela",
                password=DATOS_DE_REGISTRO["password"],
            )
        )

        self.assertEqual(
            self.client.get(reverse("material_list")).status_code, 200
        )
        self.assertEqual(
            self.client.get(reverse("operational_reports")).status_code, 403
        )

    def test_superuser_chooses_the_laboratory(self):

        otro = build_laboratory("Lab Otro", "otro@test.com")

        superusuario = User.objects.create_superuser(
            "root", password="clave", email="root@test.com"
        )

        self.client.force_login(superusuario)

        self.client.post(
            self.url,
            DATOS_DE_REGISTRO | {"laboratory": otro.pk},
        )

        usuario = LaboratoryUser.objects.get(email="daniela@laboratorio.com")

        self.assertEqual(usuario.laboratory, otro)

    def test_success_message_is_shown(self):
        """
        El sistema informa que el registro fue exitoso.
        """

        self.client.force_login(self.admin)

        response = self.client.post(self.url, DATOS_DE_REGISTRO, follow=True)

        mensajes = [str(m) for m in response.context["messages"]]

        self.assertTrue(
            any("successfully" in m for m in mensajes),
            f"No se mostro mensaje de exito: {mensajes}",
        )

    def test_error_message_is_shown_and_nothing_is_saved(self):
        """
        Con datos invalidos se informa el error y no se guarda nada.
        """

        self.client.force_login(self.admin)

        datos = DATOS_DE_REGISTRO | {"email": "invalido"}

        response = self.client.post(self.url, datos, follow=True)

        mensajes = [str(m) for m in response.context["messages"]]

        self.assertTrue(any("correct the errors" in m for m in mensajes))
        self.assertFalse(User.objects.filter(username="daniela").exists())
