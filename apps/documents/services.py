from .models import CaseFile


class CaseFileService:

    @staticmethod
    def create(
        dental_case,
        category,
        uploaded_file,
    ):

        return CaseFile.objects.create(
            dental_case=dental_case,
            category=category,
            file=uploaded_file,
            original_name=uploaded_file.name,
        )

    @staticmethod
    def create_multiple(
        dental_case,
        category,
        uploaded_files,
    ):

        created_files = []

        for uploaded_file in uploaded_files:

            case_file = (
                CaseFileService.create(
                    dental_case=dental_case,
                    category=category,
                    uploaded_file=uploaded_file,
                )
            )

            created_files.append(
                case_file
            )

        return created_files

    @staticmethod
    def delete(
        case_file,
    ):

        if case_file.file:

            case_file.file.delete(
                save=False
            )

        case_file.delete()