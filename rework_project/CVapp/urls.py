from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("upload_cv/", views.uploadCV, name="upload_cv"),
    path("feed/", views.feed, name="feed"),
    path("apply/<int:vacancy_id>/", views.apply_vacancy, name="apply"),
    path("vacancy/save/<int:vacancy_id>", views.save_vacancy, name="save"),
    path("delete_cv/<int:cv_id>", views.delete_cv, name="delete_cv"),
    path("unsave/<int:vacancy_id>", views.unsave_vacancy, name="unsave"),
    path(
        "goto_cv_improver/<int:vacancy_id>/<str:origin>/",
        views.redirect_to_cv_inprover,
        name="goto_cv_improver",
    ),
    path("mejorar-cv/", views.mejorar_cv, name="mejorar_cv"),
]