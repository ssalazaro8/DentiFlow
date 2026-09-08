from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import LaboratoryUserForm
from .models import LaboratoryUser

DATOS_VALIDOS = {
    "first_name": "Daniela",
    "last_name": "Restrepo",
    "email": "daniela@laboratorio.com",
    "phone": "+57 300 123 4567",
    "role": "TECHNICIAN",
    "status": "ACTIVE",
}


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

    def test_valid_data_is_accepted(self):
        self.assertTrue(LaboratoryUserForm(DATOS_VALIDOS).is_valid())

    def test_invalid_email_is_rejected(self):
        """
        Los datos se validan antes de guardar.
        """

        datos = DATOS_VALIDOS | {"email": "esto-no-es-un-correo"}

        form = LaboratoryUserForm(datos)

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_email_is_rejected(self):
        """
        El correo identifica al usuario, no puede repetirse.
        """

        LaboratoryUser.objects.create(**DATOS_VALIDOS)

        form = LaboratoryUserForm(DATOS_VALIDOS)

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_invalid_phone_is_rejected(self):
        """
        El telefono tiene un formato validado.
        """

        datos = DATOS_VALIDOS | {"phone": "no-es-un-telefono"}

        form = LaboratoryUserForm(datos)

        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_required_fields(self):
        """
        Nombre, apellido y correo son obligatorios.
        """

        form = LaboratoryUserForm({})

        self.assertFalse(form.is_valid())

        for campo in ("first_name", "last_name", "email"):
            with self.subTest(campo=campo):
                self.assertIn(campo, form.errors)


class LaboratoryUserViewTests(TestCase):
    """
    El flujo completo de registro desde la interfaz.
    """

    def setUp(self):
        self.url = reverse("users:create")

        self.admin = User.objects.create_user(
            username="administrador",
            password="clave-de-prueba",
        )

    def test_registration_requires_login(self):
        """
        Un anonimo no puede registrar usuarios del laboratorio.
        """

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(LaboratoryUser.objects.count(), 0)

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

        response = self.client.post(self.url, DATOS_VALIDOS, follow=True)

        self.assertEqual(response.status_code, 200)

        usuario = LaboratoryUser.objects.get(
            email="daniela@laboratorio.com"
        )

        self.assertEqual(usuario.first_name, "Daniela")
        self.assertEqual(usuario.role, "TECHNICIAN")
        self.assertEqual(usuario.status, "ACTIVE")

    def test_success_message_is_shown(self):
        """
        El sistema informa que el registro fue exitoso.
        """

        self.client.force_login(self.admin)

        response = self.client.post(self.url, DATOS_VALIDOS, follow=True)

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

        datos = DATOS_VALIDOS | {"email": "invalido"}

        response = self.client.post(self.url, datos, follow=True)

        mensajes = [str(m) for m in response.context["messages"]]

        self.assertTrue(any("correct the errors" in m for m in mensajes))
        self.assertEqual(LaboratoryUser.objects.count(), 0)
