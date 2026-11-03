from django.contrib.auth import get_user_model
from django.db import transaction

from .models import LaboratoryUser


class LaboratoryUserService:

    @staticmethod
    @transaction.atomic
    def register(data, laboratory):
        """
        Registers a laboratory user together with the account they
        sign in with.

        The role stored here is the one the system validates (FR-16).
        The account is also added to the laboratory's own lists, which
        the technician assignment still reads.
        """

        account = get_user_model().objects.create_user(
            username=data["username"],
            password=data["password"],
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )

        member = LaboratoryUser.objects.create(
            user=account,
            laboratory=laboratory,
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone=data.get("phone", ""),
            role=data["role"],
            status=data["status"],
        )

        laboratory.authorized_users.add(account)

        if member.role == "TECHNICIAN":
            laboratory.technicians.add(account)

        return member
