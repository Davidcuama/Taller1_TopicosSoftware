"""
Refactored views for user authentication and history.

This module uses Django's class‑based views (CBV) to encapsulate
behaviour for login, sign‑up and history pages.  The conversion to
CBVs simplifies routing and makes it easier to extend or override
behaviour.  For example, the LoginView overrides ``form_valid`` to
handle session management and error handling without cluttering the
template logic.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView, View

from CVapp.models import Resume, Applied_resume, Saved_vacancy
from offer.models import Vacancy
from .forms import LoginForm, SignupForm
from .models import User


class LoginView(FormView):
    """Handle user login via a form.

    If the submitted credentials are valid, the user is authenticated
    and their ID and role are stored in the session.  Otherwise, an
    appropriate error message is displayed and the form is re‑rendered.
    """

    template_name = "loginPage.html"
    form_class = LoginForm
    success_url = reverse_lazy("home")

    def form_valid(self, form: LoginForm):
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(self.request, "Usuario no encontrado.")
            return self.form_invalid(form)
        if not check_password(password, user.password):
            messages.error(self.request, "Contraseña incorrecta.")
            return self.form_invalid(form)
        # Mark user as authenticated and persist
        user.is_authenticated = True
        user.save()
        # Save session state
        self.request.session["user_id"] = user.id
        self.request.session["role"] = user.role
        return super().form_valid(form)


class SignupView(FormView):
    """Handle user registration.

    On successful registration the user is automatically logged in and
    redirected to the home page.  Password hashing is delegated to
    the SignupForm's ``save`` method.
    """

    template_name = "signupPage.html"
    form_class = SignupForm
    success_url = reverse_lazy("home")

    def form_valid(self, form: SignupForm):
        user = form.save()
        # Automatically log the user in
        self.request.session["user_id"] = user.id
        self.request.session["role"] = user.role
        user.is_authenticated = True
        user.save()
        return super().form_valid(form)


class HistoryView(TemplateView):
    """Display the history page for the current user.

    For job seekers this shows uploaded resumes, applied resumes and
    saved vacancies.  For recruiters it shows posted vacancies and the
    candidates who applied to them.  Users must be authenticated to
    access this view.
    """

    template_name = "historyPage.html"

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        # Redirect unauthenticated users to the login page
        if "user_id" not in request.session:
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        user = User.objects.get(id=self.request.session["user_id"])
        if user.role == "jobseeker":
            resumes = Resume.objects.filter(uploaded_by=user)
            applied_resumes = Applied_resume.objects.filter(resume__uploaded_by=user)
            saved_vacancies = Saved_vacancy.objects.filter(user=user)
            context.update(
                {
                    "user": user,
                    "resumes": resumes,
                    "applied_resumes": applied_resumes,
                    "saved_vacancies": saved_vacancies,
                }
            )
        else:
            vacancies = Vacancy.objects.filter(uploaded_by=user)
            vacancies_mapping: dict[Vacancy, list[Applied_resume]] = {}
            for vacancy in vacancies:
                resumes = Applied_resume.objects.filter(vacancy=vacancy)
                vacancies_mapping[vacancy] = list(resumes)
            context.update(
                {
                    "user": user,
                    "vacancies_mapping": vacancies_mapping,
                }
            )
        return context


class LogoutView(View):
    """Log the user out and redirect to the login page."""

    def get(self, request, *args, **kwargs):  # type: ignore[override]
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        return logout_view(request)


def logout_view(request):
    """Function‑based view for logging out the current user.

    Because session management is simple, a FBV is appropriate here.
    """

    if "user_id" in request.session:
        try:
            user = User.objects.get(id=request.session["user_id"])
            user.is_authenticated = False
            user.save()
        except User.DoesNotExist:
            pass
        # Clear session
        request.session.flush()
    else:
        messages.warning(request, "No hay un usuario autenticado.")
    return redirect("login")