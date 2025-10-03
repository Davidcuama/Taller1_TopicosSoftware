from django.urls import path
from . import views


urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("history/", views.HistoryView.as_view(), name="history"),
]