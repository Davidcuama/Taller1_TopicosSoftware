from django import forms


class UploadFileForm(forms.Form):
    """Form to upload a CV file and optional image with vacancy context."""

    file = forms.FileField(
        label="Sube un archivo",
        help_text="Solo archivos .pdf, .txt o .md",
        required=False,
    )
    image = forms.ImageField(
        label="Sube tu foto para el CV",
        required=False,
    )
    vacancy = forms.CharField(
        widget=forms.Textarea,
        required=True,
        label="Vacante y especificaciones",
    )
    cv_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Texto del CV",
    )


class SelectOutputFormat(forms.Form):
    """Form for choosing an output format for the improved CV."""

    outputFormat = forms.ChoiceField(
        choices=[("txt", "TXT"), ("docx", "DOCX"), ("pdf", "PDF")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )