from django import forms

from .models import CaseFile


class MultipleFileInput(
    forms.ClearableFileInput
):

    allow_multiple_selected = True


class MultipleFileField(
    forms.FileField
):

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        kwargs.setdefault(
            "widget",
            MultipleFileInput(),
        )

        super().__init__(
            *args,
            **kwargs,
        )

    def clean(
        self,
        data,
        initial=None,
    ):

        single_file_clean = super().clean

        if isinstance(
            data,
            (list, tuple),
        ):

            return [
                single_file_clean(
                    uploaded_file,
                    initial,
                )
                for uploaded_file in data
            ]

        return [
            single_file_clean(
                data,
                initial,
            )
        ]


class CaseFileUploadForm(
    forms.Form
):

    category = forms.ChoiceField(
        choices=CaseFile.Category.choices,
        label="File Category",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    files = MultipleFileField(
        label="Files",
        required=True,
        widget=MultipleFileInput(
            attrs={
                "class": "form-control",
                "accept": (
                    ".stl,"
                    ".jpg,"
                    ".jpeg,"
                    ".png,"
                    ".pdf,"
                    ".doc,"
                    ".docx"
                ),
            }
        ),
    )

    def clean_files(self):

        files = self.cleaned_data[
            "files"
        ]

        max_size = (
            25 * 1024 * 1024
        )

        for uploaded_file in files:

            if uploaded_file.size > max_size:

                raise forms.ValidationError(
                    (
                        f"{uploaded_file.name} "
                        "exceeds the maximum "
                        "allowed size of 25 MB."
                    )
                )

        return files