from django.urls import path
from . import views


urlpatterns = [
    path("upload_vacancies/", views.upload_vacancies, name="upload_vacancies"),
    path("upload_cvs/", views.uploadCVS, name="upload_cvs"),
    path("open_vacancies/<int:vacancy_id>", views.change_state_vacancy, name="change_vacancy_state"),
    path("accept_resume/<int:resume_id>", views.accept_resume, name="accept_resume"),
    path("reject_resume/<int:resume_id>", views.reject_resume, name="reject_resume"),
]