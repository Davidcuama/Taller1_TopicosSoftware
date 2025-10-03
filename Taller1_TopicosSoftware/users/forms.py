from django import forms
from django.contrib.auth.hashers import make_password
from .models import User


class SignupForm(forms.ModelForm):
    """Form for registering a new user.

    Overrides the default save method to hash the password before
    persisting the user instance to the database.
    """

    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "role",
            "profile_image",
            "linkedin_id",
        ]

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        # Hash the password using Django's hashers
        user.password = make_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Simple login form capturing username and password."""

    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)