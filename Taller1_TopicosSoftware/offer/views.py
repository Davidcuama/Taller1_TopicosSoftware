"""
Views for the offer app.

This module refactors the original function‑based views to use
strategies and services for embedding computation.  The uploadCVS
function ranks multiple CVs against a vacancy using cosine similarity
and returns a sorted ranking.  Dependency inversion is applied
through the use of an embedding service defined in CVapp.services.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect

from users.models import User
from CVapp.models import Applied_resume, Resume
from .models import Vacancy
from .forms import UploadFileFormOffer, UploadVacancyForm

from CVapp.services import (
    FileExtractionStrategy,
    PdfExtractionStrategy,
    TextExtractionStrategy,
    EmbeddingService,
    OpenAIEmbeddingService,
    MockEmbeddingService,
    cosine_similarity,
)

# Import the global notification subject to notify candidates when their
# resumes are accepted or rejected.  This implements an Observer pattern
# where the subject forwards events to all registered observers (e.g.,
# persisting a notification or sending an email).  See
# notifications/services.py for details.
from notifications.services import notification_subject

# Choose embedding service based on environment
try:
    if getattr(settings, "OPENAI_API_KEY", None):
        _embedding_service: EmbeddingService = OpenAIEmbeddingService(settings.OPENAI_API_KEY)  # type: ignore[arg-type]
    else:
        raise AttributeError
except Exception:
    _embedding_service = MockEmbeddingService()


def _get_extraction_strategy(filename: str) -> FileExtractionStrategy:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return PdfExtractionStrategy()
    return TextExtractionStrategy()


def uploadCVS(request):  # noqa: N802
    """Upload and rank multiple CVs against a vacancy description.

    The user provides a vacancy text in the POST data and one or more
    uploaded files.  The function extracts text from each file using
    the appropriate strategy, computes embeddings via the global
    embedding service, and returns a ranking sorted by cosine
    similarity.
    """
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    best_cv: Optional[Dict[str, object]] = None
    best_score: float = -1.0
    ranking: List[Dict[str, object]] = []
    if request.method == "POST":
        form = UploadFileFormOffer(request.POST, request.FILES)
        if form.is_valid() and request.FILES:
            vacancy_text = request.POST.get("vacancy", "")
            files = request.FILES.getlist("file")
            if not vacancy_text.strip():
                messages.warning(request, "No hay un texto de vacante proporcionado.")
            elif not files:
                messages.warning(request, "No se seleccionaron archivos.")
            else:
                # Compute embedding for vacancy text
                vacancy_embedding = _embedding_service.embed(vacancy_text)
                for uploaded_file in files:
                    strategy = _get_extraction_strategy(uploaded_file.name)
                    cv_text = strategy.extract(uploaded_file)
                    cv_embedding = _embedding_service.embed(cv_text)
                    score = cosine_similarity(vacancy_embedding, cv_embedding)
                    ranking.append({
                        "filename": uploaded_file.name,
                        "cv_text": cv_text,
                        "score": score,
                    })
                    if score > best_score:
                        best_score = score
                        best_cv = {
                            "filename": uploaded_file.name,
                            "cv_text": cv_text,
                            "score": score,
                        }
                # Sort ranking descending by score
                ranking.sort(key=lambda x: x["score"], reverse=True)
                messages.success(request, "Todos los archivos fueron procesados correctamente.")
                return render(
                    request,
                    "matchingPage.html",
                    {
                        "form": form,
                        "user": user,
                        "ranking": ranking,
                        "best_cv": best_cv,
                        "vacancy": vacancy_text,
                    },
                )
        else:
            messages.warning(request, "Error en la carga del formulario.")
    else:
        form = UploadFileFormOffer()
    return render(request, "matchingPage.html", {"form": form, "user": user})


def upload_vacancies(request):  # noqa: N802
    """Create a new vacancy posted by a recruiter."""
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    if request.method == "POST":
        form = UploadVacancyForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            description = form.cleaned_data["description"]
            requirements = form.cleaned_data.get("requirements", "")
            extracted_text = f"{description} {requirements}".strip()
            embedding = _embedding_service.embed(extracted_text).tobytes()
            vacancy = Vacancy(
                title=title,
                description=description,
                requirements=requirements,
                uploaded_by=user,
                embedding=embedding,
            )
            vacancy.save()
            messages.success(request, "Vacante subida con éxito.")
            return redirect("history")
        messages.warning(request, "Error al subir la vacante.")
    else:
        form = UploadVacancyForm()
    return render(request, "offer.html", {"form": form, "user": user})


def change_state_vacancy(request, vacancy_id: int):  # noqa: N802
    """Toggle the state of a vacancy between open and closed."""
    if "user_id" not in request.session:
        return redirect("login")
    vacancy = Vacancy.objects.get(id=vacancy_id)
    if vacancy.uploaded_by.id != request.session["user_id"]:
        messages.error(request, "No tienes permiso para cambiar el estado de esta vacante.")
        return redirect("history")
    if vacancy.state == "open":
        vacancy.state = "closed"
        vacancy.save()
        messages.success(request, "Vacante cerrada con éxito.")
        return redirect("history")
    if vacancy.state == "closed":
        vacancy.state = "open"
        vacancy.save()
        messages.success(request, "Vacante abierta con éxito.")
    return redirect("history")


def accept_resume(request, resume_id: int):  # noqa: N802
    """Accept an applied resume for a vacancy."""
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    resume = Applied_resume.objects.get(id=resume_id)
    if resume.vacancy.uploaded_by.id != user.id:
        messages.error(request, "No tienes permiso para aceptar este CV.")
        return redirect("history")
    if resume.state != "applied":
        messages.error(request, "Este CV ya ha sido procesado.")
        return redirect("history")
    resume.state = "accepted"
    resume.save()
    # Notify the candidate that their resume has been accepted.
    # The message includes the title of the vacancy for context.
    notification_subject.notify(
        resume.resume.uploaded_by,
        f"Tu CV para la vacante '{resume.vacancy.title}' ha sido aceptado. Nos pondremos en contacto contigo pronto."
    )
    messages.success(request, "CV aceptado con éxito.")
    return redirect("history")


def reject_resume(request, resume_id: int):  # noqa: N802
    """Reject an applied resume for a vacancy."""
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    resume = Applied_resume.objects.get(id=resume_id)
    if resume.vacancy.uploaded_by.id != user.id:
        messages.error(request, "No tienes permiso para rechazar este CV.")
        return redirect("history")
    if resume.state != "applied":
        messages.error(request, "Este CV ya ha sido procesado.")
        return redirect("history")
    resume.state = "rejected"
    resume.save()
    # Notify the candidate that their resume has been rejected.
    notification_subject.notify(
        resume.resume.uploaded_by,
        f"Tu CV para la vacante '{resume.vacancy.title}' ha sido rechazado. ¡Gracias por participar!"
    )
    messages.success(request, "CV rechazado con éxito.")
    return redirect("history")