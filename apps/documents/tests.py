from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.dental_cases.models import DentalCase, DentalCaseFile
from apps.laboratories.models import Laboratory

from .models import CaseFile

CONTENIDO = b"contenido confidencial del caso"


class CaseFileAccessTests(TestCase):
    """
    FR-24: solo los usuarios asociados a un caso ven y descargan sus
    archivos.
    """

    def setUp(self):
        self.laboratory = Laboratory.objects.create(
            name="Lab Propio",
            email="propio@test.com",
            phone="1",
            city="Medellin",
            address="Calle 1",
            service="CROWN",
        )

        # Tecnico autorizado en el laboratorio de destino.
        self.tecnico = User.objects.create_user("tecnico", password="clave")
        self.laboratory.authorized_users.add(self.tecnico)

        # Cuenta que registro el caso.
        self.solicitante = User.objects.create_user(
            "solicitante", password="clave"
        )

        # Usuario sin ninguna relacion con el caso.
        self.intruso = User.objects.create_user("intruso", password="clave")

        self.case = DentalCase.objects.create(
            case_number="SEC-001",
            clinic_name="Clinica",
            requested_by="Dr. Test",
            service_type="CROWN",
            description="Caso con adjuntos",
            status=DentalCase.Status.IN_PROGRESS,
            laboratory=self.laboratory,
            created_by=self.solicitante,
            due_date=timezone.now().date() + timedelta(days=7),
        )

        self.case_file = CaseFile.objects.create(
            dental_case=self.case,
            file=SimpleUploadedFile("radiografia.txt", CONTENIDO),
            original_name="radiografia.txt",
        )

        self.dental_case_file = DentalCaseFile.objects.create(
            case=self.case,
            file=SimpleUploadedFile("molde.txt", CONTENIDO),
        )

        self.url_listado = reverse(
            "case_file_list", args=[self.case.id]
        )
        self.url_descarga = reverse(
            "case_file_download", args=[self.case.id, self.case_file.id]
        )
        self.url_descarga_fr24 = reverse(
            "download_file", args=[self.dental_case_file.id]
        )

    # --- Usuarios autorizados ---

    def test_technician_of_the_laboratory_can_download(self):
        """
        Un tecnico del laboratorio de destino descarga el archivo.
        """

        self.client.force_login(self.tecnico)

        response = self.client.get(self.url_descarga)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            b"".join(response.streaming_content), CONTENIDO
        )

    def test_case_author_can_download(self):
        """
        La cuenta que registro el caso tambien accede.
        """

        self.client.force_login(self.solicitante)

        self.assertEqual(
            self.client.get(self.url_descarga).status_code, 200
        )

    def test_superuser_can_download(self):
        """
        El superusuario no tiene restriccion.
        """

        admin = User.objects.create_superuser(
            "admin", password="clave", email="admin@test.com"
        )

        self.client.force_login(admin)

        self.assertEqual(
            self.client.get(self.url_descarga).status_code, 200
        )

    def test_authorized_user_sees_the_file_list(self):
        """
        El flujo completo: entrar al caso y ver sus archivos.
        """

        self.client.force_login(self.tecnico)

        response = self.client.get(self.url_listado)

        self.assertEqual(response.status_code, 200)
        self.assertIn("radiografia", response.content.decode())

    # --- Usuarios no asociados ---

    def test_unrelated_user_cannot_download(self):
        """
        Un usuario logueado sin relacion con el caso recibe 403.
        """

        self.client.force_login(self.intruso)

        self.assertEqual(
            self.client.get(self.url_descarga).status_code, 403
        )

    def test_unrelated_user_cannot_list_files(self):
        """
        Tampoco puede ver que archivos existen.
        """

        self.client.force_login(self.intruso)

        self.assertEqual(
            self.client.get(self.url_listado).status_code, 403
        )

    def test_unrelated_user_gets_an_explanation(self):
        """
        El rechazo explica el motivo, no falla en seco.
        """

        self.client.force_login(self.intruso)

        response = self.client.get(self.url_descarga)

        self.assertIn(
            "not authorized",
            response.content.decode().lower(),
        )

    def test_unrelated_user_cannot_delete_files(self):
        """
        Borrar tambien esta protegido, no solo leer.
        """

        self.client.force_login(self.intruso)

        response = self.client.get(
            reverse(
                "case_file_delete",
                args=[self.case.id, self.case_file.id],
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            CaseFile.objects.filter(pk=self.case_file.pk).exists()
        )

    # --- Usuarios anonimos ---

    def test_anonymous_cannot_reach_the_files(self):
        """
        Sin sesion no se llega a ninguna de las vistas de archivos.
        """

        for url in (
            self.url_listado,
            self.url_descarga,
            self.url_descarga_fr24,
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)

    # --- Ruta de descarga de FR-24 ---

    def test_fr24_download_is_protected_too(self):
        """
        La descarga directa de FR-24 aplica la misma regla.
        """

        self.client.force_login(self.intruso)

        self.assertEqual(
            self.client.get(self.url_descarga_fr24).status_code, 403
        )

    def test_fr24_download_returns_the_right_file(self):
        """
        El archivo descargado es el del caso solicitado.
        """

        self.client.force_login(self.tecnico)

        response = self.client.get(self.url_descarga_fr24)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            b"".join(response.streaming_content), CONTENIDO
        )

    def test_missing_file_is_reported(self):
        """
        Un archivo inexistente responde 404, no un error del servidor.
        """

        self.client.force_login(self.tecnico)

        response = self.client.get(
            reverse("download_file", args=[9999])
        )

        self.assertEqual(response.status_code, 404)
