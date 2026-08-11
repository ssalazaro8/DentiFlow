from .models import CaseFile


class CaseFileSelector:

    @staticmethod
    def get_all():

        return (
            CaseFile.objects
            .select_related(
                "dental_case"
            )
            .all()
        )

    @staticmethod
    def get_by_id(
        file_id,
    ):

        return (
            CaseFile.objects
            .select_related(
                "dental_case"
            )
            .filter(
                id=file_id
            )
            .first()
        )

    @staticmethod
    def get_by_case(
        dental_case,
    ):

        return (
            CaseFile.objects
            .filter(
                dental_case=dental_case
            )
            .order_by(
                "-uploaded_at"
            )
        )