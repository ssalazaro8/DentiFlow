from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from .selectors import get_case_file_by_id


@login_required
def download_case_file_view(request, file_id: int):
    case_file = get_case_file_by_id(file_id=file_id)

    if not case_file.file or not case_file.file.storage.exists(case_file.file.name):
        raise Http404("El archivo solicitado no existe en el servidor.")

    return FileResponse(
        case_file.file.open("rb"),
        as_attachment=True,
        filename=case_file.filename,
    )