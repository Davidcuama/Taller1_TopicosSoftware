from django import forms


class UploadFileFormOffer(forms.Form):
    """Form for uploading multiple CV files to rank against a vacancy."""

    file = forms.FileField(
        label="Sube un archivo",
        help_text="Solo archivos .pdf, .txt o .md",
        required=False,
    )
    vacancy = forms.Textarea()


class UploadVacancyForm(forms.Form):
    """Form for posting a new vacancy."""

    title = forms.CharField(max_length=100, required=True)
    description = forms.CharField(widget=forms.Textarea, required=True)
    requirements = forms.CharField(widget=forms.Textarea, required=False)