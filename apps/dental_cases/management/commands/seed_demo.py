"""
Loads demonstration data: twelve weeks of dental cases for one
laboratory, with deliveries on time and late, workflow history,
technician assignments and material consumption.

Usage:
    py manage.py seed_demo
    py manage.py seed_demo --laboratory "Laboratorio DentiFlow"
    py manage.py seed_demo --password <password>   (also creates demo accounts)
    py manage.py seed_demo --reset                 (replaces the demo cases)

Every case it creates starts with SEED-, so running it again does not
duplicate anything and --reset only removes what this command made.
"""

import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.clinics.models import Clinic
from apps.dental_cases.models import (
    DeliveryRegistration,
    DentalCase,
    TechnicianAssignment,
)
from apps.inventory.models import Material, MaterialConsumption
from apps.laboratories.models import Laboratory
from apps.users.models import LaboratoryUser
from apps.users.services import LaboratoryUserService
from apps.workflow.models import Workflow, WorkflowUpdate

PREFIX = "SEED-"
WEEKS = 12

CLINICS = [
    ("Sonrisa Total", "901100201", "Medellin"),
    ("OdontoCare", "901100202", "Envigado"),
    ("Dental Plus", "901100203", "Bello"),
]

MATERIALS = [
    ("Zirconia", "GRAM", 5000, 800),
    ("Composite resin", "MILLILITER", 2000, 300),
    ("Modeling wax", "GRAM", 3000, 400),
    ("Titanium implant", "UNIT", 60, 10),
]

# What each service consumes: material name and a range of quantities.
RECIPES = {
    "CROWN": [("Zirconia", 8, 15), ("Modeling wax", 5, 10)],
    "BRIDGE": [("Zirconia", 20, 35), ("Modeling wax", 10, 20)],
    "IMPLANT": [("Titanium implant", 1, 2), ("Zirconia", 6, 12)],
    "VENEER": [("Composite resin", 3, 6)],
    "ORTHODONTICS": [("Composite resin", 5, 10), ("Modeling wax", 5, 8)],
}

DESCRIPTIONS = {
    "CROWN": "Zirconia crown, shade A2",
    "BRIDGE": "Three unit bridge, shade A3",
    "IMPLANT": "Implant crown with titanium abutment",
    "VENEER": "Porcelain veneers for the upper incisors",
    "ORTHODONTICS": "Clear aligner models",
}

STAGES = ["RECEIVED", "DESIGN", "PRINTING", "QC", "SHIPPED"]
PROGRESS = {"RECEIVED": 10, "DESIGN": 35, "PRINTING": 60, "QC": 85, "SHIPPED": 100}

DEMO_ACCOUNTS = [
    ("demo_admin", "Laura", "Gomez", "ADMIN"),
    ("demo_recepcion", "Camila", "Rios", "RECEPTIONIST"),
    ("demo_tecnico", "Andres", "Mejia", "TECHNICIAN"),
]
DEMO_CLINIC_ACCOUNT = "demo_clinica"


def at(day, hour):
    return timezone.make_aware(datetime.combine(day, time(hour)))


class Command(BaseCommand):

    help = "Loads twelve weeks of demonstration data for one laboratory."

    def add_arguments(self, parser):
        parser.add_argument("--laboratory", default="Laboratorio DentiFlow")
        parser.add_argument("--password", help="Creates the demo accounts with this password.")
        parser.add_argument("--reset", action="store_true", help="Replaces the demo cases.")
        parser.add_argument("--seed", type=int, default=34)

    @transaction.atomic
    def handle(self, *args, **options):

        self.random = random.Random(options["seed"])
        self.today = timezone.localdate()

        if options["reset"]:
            removed = self.reset()
            self.stdout.write(f"Removed {removed} demo cases.")

        if DentalCase.objects.filter(case_number__startswith=PREFIX).exists():
            raise CommandError(
                "The demo cases are already loaded. Use --reset to load them again."
            )

        self.laboratory = self.get_laboratory(options["laboratory"])
        self.clinics = self.get_clinics()
        self.materials = self.get_materials()

        if options["password"]:
            self.create_accounts(options["password"])

        self.staff = self.find_staff()
        self.technicians = self.find_technicians()

        created = self.create_cases()

        self.stdout.write(self.style.SUCCESS(
            f"Loaded {created} demo cases into {self.laboratory.name}."
        ))

    # --- reference data ---

    def reset(self):

        cases = DentalCase.objects.filter(case_number__startswith=PREFIX)
        ids = list(cases.values_list("id", flat=True))

        MaterialConsumption.objects.filter(dental_case_id__in=ids).delete()
        DeliveryRegistration.objects.filter(dental_case_id__in=ids).delete()
        cases.delete()

        return len(ids)

    def get_laboratory(self, name):

        laboratory, _ = Laboratory.objects.get_or_create(
            name=name,
            defaults={
                "email": "lab@dentiflow.com",
                "phone": "6045550000",
                "city": "Medellin",
                "address": "Calle 10 # 43-20",
                "service": "CROWN",
            },
        )

        return laboratory

    def get_clinics(self):

        clinics = list(Clinic.objects.filter(is_active=True))

        for name, nit, city in CLINICS:

            clinic, created = Clinic.objects.get_or_create(
                nit=nit,
                defaults={
                    "name": name,
                    "email": f"contacto@{name.lower().replace(' ', '')}.com",
                    "phone": "6045551234",
                    "address": "Carrera 43A # 1-50",
                    "city": city,
                    "contact_person": "Recepcion",
                },
            )

            if created:
                clinics.append(clinic)

        return clinics

    def get_materials(self):

        materials = {}

        for name, unit, stock, reorder in MATERIALS:

            materials[name], _ = Material.objects.get_or_create(
                name=name,
                defaults={
                    "unit_type": unit,
                    "stock_quantity": Decimal(stock),
                    "reorder_level": Decimal(reorder),
                },
            )

        return materials

    def create_accounts(self, password):

        users = get_user_model().objects

        for username, first_name, last_name, role in DEMO_ACCOUNTS:

            if users.filter(username=username).exists():
                continue

            LaboratoryUserService.register(
                {
                    "username": username,
                    "password": password,
                    "email": f"{username}@dentiflow.com",
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role,
                    "status": "ACTIVE",
                },
                self.laboratory,
            )

            self.stdout.write(f"Created {username} ({role}).")

        if not users.filter(username=DEMO_CLINIC_ACCOUNT).exists():

            account = users.create_user(
                DEMO_CLINIC_ACCOUNT,
                password=password,
                email=f"{DEMO_CLINIC_ACCOUNT}@dentiflow.com",
                first_name="Sonrisa",
                last_name="Total",
            )
            clinic = Clinic.objects.get(nit=CLINICS[0][1])
            clinic.users.add(account)

            self.stdout.write(f"Created {DEMO_CLINIC_ACCOUNT} (clinic {clinic.name}).")

    def find_staff(self):
        """
        Someone of the laboratory to register deliveries and updates.
        """

        members = LaboratoryUser.objects.filter(
            laboratory=self.laboratory, user__isnull=False
        ).select_related("user")

        for role in ("ADMIN", "RECEPTIONIST", "TECHNICIAN"):
            for member in members:
                if member.role == role:
                    return member.user

        user = (
            self.laboratory.authorized_users.first()
            or get_user_model().objects.filter(is_superuser=True).first()
        )

        if user is None:
            raise CommandError(
                "Nobody works in this laboratory yet. Run the command with "
                "--password to create the demo accounts."
            )

        return user

    def find_technicians(self):

        technicians = list(self.laboratory.technicians.all())

        return technicians or [self.staff]

    # --- cases ---

    def create_cases(self):

        number = 0
        monday = self.today - timedelta(days=self.today.weekday())

        for week in range(WEEKS - 1, -1, -1):

            start = monday - timedelta(weeks=week)

            # The volume grows slowly, as a laboratory that gains clinics.
            amount = self.random.randint(3, 5) + (WEEKS - week) // 3

            for _ in range(amount):

                received = start + timedelta(days=self.random.randint(0, 5))

                if received > self.today:
                    continue

                number += 1
                self.create_case(f"{PREFIX}{number:04d}", received)

        return number

    def create_case(self, case_number, received):

        rng = self.random
        service = rng.choice(list(RECIPES))
        clinic = rng.choice(self.clinics)
        due_date = received + timedelta(days=rng.randint(7, 12))
        age = (self.today - received).days

        dental_case = DentalCase.objects.create(
            case_number=case_number,
            clinic=clinic,
            clinic_name=clinic.name,
            requested_by=clinic.contact_person or clinic.name,
            laboratory=self.laboratory,
            service_type=service,
            description=DESCRIPTIONS[service],
            due_date=due_date,
            status=DentalCase.Status.SUBMITTED,
        )

        # created_at is filled on creation, so it is moved afterwards;
        # the object keeps it too, or the next save would undo it.
        dental_case.created_at = at(received, rng.randint(8, 16))
        DentalCase.objects.filter(pk=dental_case.pk).update(
            created_at=dental_case.created_at
        )

        # The newest cases are still waiting for the laboratory.
        if age <= 1 and rng.random() < 0.7:
            return

        # A few cases are rejected or cancelled along the way.
        if rng.random() < 0.05:
            dental_case.status = rng.choice(
                [DentalCase.Status.REJECTED, DentalCase.Status.CANCELLED]
            )
            if dental_case.status == DentalCase.Status.REJECTED:
                dental_case.acceptance_status = DentalCase.AcceptanceStatus.REJECTED
                dental_case.rejection_reason = "The impression arrived damaged."
                dental_case.rejected_at = at(received, 17)
            dental_case.save()
            return

        accepted = at(received + timedelta(days=rng.randint(0, 1)), 9)
        dental_case.acceptance_status = DentalCase.AcceptanceStatus.ACCEPTED
        dental_case.accepted_at = accepted

        # Most cases take between 4 and 8 days; some get delayed.
        production_days = rng.randint(4, 8) + (rng.randint(4, 7) if rng.random() < 0.15 else 0)
        finished = accepted + timedelta(days=production_days)

        # Some cases of the last two weeks got stuck and are overdue.
        if 8 <= age <= 14 and rng.random() < 0.35:
            finished = at(self.today + timedelta(days=rng.randint(3, 5)), 15)

        if finished.date() < self.today:
            stage = "SHIPPED"
            dental_case.status = DentalCase.Status.DELIVERED
        elif finished.date() - timedelta(days=2) < self.today:
            stage = "QC"
            dental_case.status = DentalCase.Status.COMPLETED
        else:
            done = (self.today - accepted.date()).days / production_days
            stage = STAGES[min(3, max(1, int(done * 4)))]
            dental_case.status = DentalCase.Status.IN_PROGRESS

        dental_case.save()

        technician = rng.choice(self.technicians)
        TechnicianAssignment.objects.create(dental_case=dental_case, technician=technician)

        self.create_workflow(dental_case, stage, accepted, finished, technician)
        self.consume_materials(dental_case, service, accepted, stage, technician)

        if dental_case.status == DentalCase.Status.DELIVERED:

            delivery = DeliveryRegistration.objects.create(
                dental_case=dental_case,
                destination_clinic=clinic,
                registered_by=self.staff,
                completed_at=finished - timedelta(hours=4),
                notes="Delivered to the clinic reception.",
            )

            DeliveryRegistration.objects.filter(pk=delivery.pk).update(
                delivered_at=finished
            )

    def create_workflow(self, dental_case, stage, accepted, finished, technician):

        reached = STAGES[: STAGES.index(stage) + 1]
        step = (finished - accepted) / len(STAGES)

        workflow = Workflow.objects.create(
            dental_case=dental_case,
            current_stage=stage,
            progress_percentage=PROGRESS[stage],
        )

        previous = ""

        for index, name in enumerate(reached):

            update = WorkflowUpdate.objects.create(
                workflow=workflow,
                previous_stage=previous,
                stage=name,
                progress_percentage=PROGRESS[name],
                comment="" if index else "Case received at the laboratory.",
                updated_by=technician,
            )

            WorkflowUpdate.objects.filter(pk=update.pk).update(
                created_at=min(accepted + step * index, timezone.now())
            )

            previous = name

    def consume_materials(self, dental_case, service, accepted, stage, technician):

        if stage in ("RECEIVED", "DESIGN"):
            return

        for name, low, high in RECIPES[service]:

            consumption = MaterialConsumption.objects.create(
                dental_case=dental_case,
                material=self.materials[name],
                quantity=Decimal(self.random.randint(low, high)),
                registered_by=technician,
            )

            MaterialConsumption.objects.filter(pk=consumption.pk).update(
                consumed_at=min(
                    accepted + timedelta(days=self.random.randint(1, 3)),
                    timezone.now(),
                )
            )
