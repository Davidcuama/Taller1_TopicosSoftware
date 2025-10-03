"""
Views for uploading, improving and managing CVs.

This module refactors the original function‑based views to use
strategies and services defined in ``services.py``.  Text extraction
from different file types is delegated to ``FileExtractionStrategy``
implementations, and embedding computation is provided via an
``EmbeddingService``.  These abstractions illustrate the Strategy
pattern and Dependency Inversion principle.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional
import numpy as np

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect

from users.models import User
from offer.models import Vacancy
from .models import Resume, Applied_resume, Saved_vacancy
from .forms import SelectOutputFormat, UploadFileForm
from .services import (
    PdfExtractionStrategy,
    TextExtractionStrategy,
    FileExtractionStrategy,
    EmbeddingService,
    OpenAIEmbeddingService,
    MockEmbeddingService,
    cosine_similarity,
)

# Select an embedding service based on environment.  If an API key
# exists use the OpenAI service; otherwise fallback to a mock.
_embedding_service: EmbeddingService
try:
    if getattr(settings, "OPENAI_API_KEY", None):
        _embedding_service = OpenAIEmbeddingService(settings.OPENAI_API_KEY)  # type: ignore[arg-type]
    else:
        raise AttributeError
except Exception:
    _embedding_service = MockEmbeddingService()


def _get_extraction_strategy(filename: str) -> FileExtractionStrategy:
    """Return an appropriate extraction strategy based on file extension."""
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return PdfExtractionStrategy()
    return TextExtractionStrategy()


def home(request):
    """Render the home page if the user is authenticated."""
    if "user_id" in request.session:
        user = User.objects.get(id=request.session["user_id"])
        context = {"user": user}
        
        # Add additional context for recruiters
        if user.role == "recruiter":
            context["open_vacancies_count"] = user.vacancies.filter(state="open").count()
        
        return render(request, "home.html", context)
    return redirect("login")


def feed(request):
    """Show open vacancies to authenticated users."""
    if "user_id" in request.session:
        user = User.objects.get(id=request.session["user_id"])
        vacancies = Vacancy.objects.filter(state="open").order_by("-uploaded_at")
        return render(request, "feed.html", {"user": user, "vacancies": vacancies})
    return redirect("login")


def uploadCV(request):  # noqa: N802
    """Handle uploading of CVs for improvement.

    Uses the Strategy pattern to extract text from either PDF or text
    files.  Embeddings are computed via the global embedding service.
    """
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])

    initial_data: Dict[str, str] = {}
    vacancy_id = request.GET.get("vacancy_id")
    if vacancy_id:
        try:
            saved_vacancy = Vacancy.objects.get(id=vacancy_id)
            initial_data["vacancy"] = f"{saved_vacancy.description} \n {saved_vacancy.requirements}"
        except Vacancy.DoesNotExist:
            pass

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES.get("file")
            image = request.FILES.get("image")
            vacancy_text = form.cleaned_data["vacancy"]
            cv_text = form.cleaned_data["cv_text"]

            # Extract or read text from uploaded file or manual input
            extracted_text: Optional[str] = None
            if uploaded_file:
                strategy = _get_extraction_strategy(uploaded_file.name)
                extracted_text = strategy.extract(uploaded_file)
            elif cv_text.strip():
                extracted_text = cv_text
            else:
                messages.warning(request, "No hay un CV inicial")
                return render(
                    request,
                    "JobseekerPage.html",
                    {"form": form, "user": user},
                )

            # Compute embedding
            embedding = _embedding_service.embed(extracted_text).tobytes()

            Resume.objects.create(
                version="1.0",
                name=uploaded_file.name if uploaded_file else "Manual Entry",
                vacancy_text=vacancy_text,
                image=image,
                extracted_text=extracted_text,
                upgraded_cv="",
                uploaded_by=user,
                embedding=embedding,
            )

            messages.success(request, "CV subido y procesado con éxito")
        else:
            print(form.errors)
            messages.error(request, "Formulario no válido")
    else:
        form = UploadFileForm(initial=initial_data)

    return render(request, "JobseekerPage.html", {"form": form, "user": user, "vacancy": initial_data.get("vacancy", "")})


def mejorar_cv(request):  # noqa: N802
    """Improve the most recently uploaded CV using GPT and offer download options."""
    if "user_id" not in request.session:
        return redirect("login")

    user = User.objects.get(id=request.session["user_id"])
    resume = Resume.objects.filter(uploaded_by=user).last()
    if not resume:
        messages.error(request, "No has subido un CV aún.")
        return redirect("upload_cv")

    vacancy_text = resume.vacancy_text
    cv_text = resume.extracted_text

    # Build prompt for GPT
    prompt = (
        f"VACANTE:\n{vacancy_text}\n\n"
        f"CV ACTUAL:\n{cv_text}\n\n"
        """
        Eres un experto en redacción de currículums optimizados para vacantes específicas. A partir del CV actual y la descripción de la vacante que te proporciono, realiza una versión mejorada del CV que:
        - Destaque con claridad las habilidades, experiencias y logros relevantes para la vacante.
        - Reorganice o reformule el contenido para hacerlo más atractivo, convincente y profesional.
        - Elimine y omita la información que no aporte valor a la postulación.
        - Use un lenguaje proactivo, orientado a resultados y alineado con la terminología de la vacante.
        - Mantenga intacta la información personal como nombre, correo y teléfono.
        - No inventes datos, títulos ni experiencia que no estén presentes en el CV original.
        - NO incluyas ninguna introducción, comentario, conclusión ni frases como "Aquí está el CV mejorado". Solo entrega el texto final del currículum optimizado y estructurado.
        - Mejora el orden y los títulos de las secciones si es necesario para que el CV sea más claro y enfocado.
        Tu objetivo es que el CV sea visual y estratégicamente más potente para aplicar a esta vacante específica.
        """
    )

    # Ask the OpenAI Chat API for the improved CV
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7,
        )
        new_cv: str = response.choices[0].message.content.strip()
    except Exception:
        # Fallback: do not modify the CV if OpenAI is unavailable
        new_cv = cv_text
        messages.warning(
            request,
            "No se pudo acceder al servicio de IA, se mostrará el CV original.",
        )

    resume.upgraded_cv = new_cv
    resume.save()

    if request.method == "POST":
        form = SelectOutputFormat(request.POST)
        if form.is_valid():
            format_selected = form.cleaned_data["outputFormat"]
            if format_selected == "pdf":
                return _generate_pdf_response(resume.upgraded_cv)
            if format_selected == "docx":
                return _generate_docx_response(resume.upgraded_cv)
            if format_selected == "txt":
                return _generate_txt_response(resume.upgraded_cv)
    else:
        form = SelectOutputFormat()

    return render(request, "jobseekerPage.html", {"form": form})


def apply_vacancy(request, vacancy_id: int):  # noqa: N802
    """Allow a job seeker to apply to a vacancy with a selected CV."""
    if "user_id" not in request.session:
        return redirect("login")

    user = User.objects.get(id=request.session["user_id"])
    vacancy = Vacancy.objects.get(id=vacancy_id)
    resumes = Resume.objects.filter(uploaded_by=user)
    if not resumes.exists():
        messages.warning(request, "No tienes un CV subido")
        return redirect("upload_cv")
    if request.method == "POST":
        selected_resume_id = request.POST.get("resume_id")
        resume = resumes.filter(id=selected_resume_id).first()
        if not resume:
            messages.error(request, "Debes seleccionar un CV válido.")
            return redirect("apply", vacancy_id=vacancy_id)
        # Compute embeddings if missing
        resume_emb = None
        vacancy_emb = None
        if resume.embedding:
            resume_emb = np.frombuffer(resume.embedding, dtype=np.float32)
        else:
            resume_emb = _embedding_service.embed(resume.extracted_text)
            resume.embedding = resume_emb.tobytes()
            resume.save()
        if vacancy.embedding:
            vacancy_emb = np.frombuffer(vacancy.embedding, dtype=np.float32)
        else:
            combined = vacancy.description + " " + vacancy.requirements
            vacancy_emb = _embedding_service.embed(combined)
            vacancy.embedding = vacancy_emb.tobytes()
            vacancy.save()
        # Create application
        match = cosine_similarity(resume_emb, vacancy_emb)
        if Applied_resume.objects.filter(resume=resume, vacancy=vacancy).exists():
            messages.warning(request, "Ya has aplicado a esta vacante con este CV")
            return redirect("feed")
        Applied_resume.objects.create(
            resume=resume,
            vacancy=vacancy,
            match_rate=match,
        )
        messages.success(request, "Has aplicado a la vacante con éxito")
        return redirect("feed")
    return render(
        request,
        "select_resume.html",
        {"vacancy": vacancy, "resumes": resumes, "user": user},
    )


def delete_cv(request, cv_id: int):  # noqa: N802
    """Delete a CV if it hasn't been used for an application."""
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    resume = Resume.objects.get(id=cv_id, uploaded_by=user)
    if Applied_resume.objects.filter(resume=resume).exists():
        messages.warning(
            request, "No puedes eliminar un CV que ya has usado para aplicar a una vacante"
        )
        return redirect("history")
    resume.delete()
    messages.success(request, "CV eliminado con éxito")
    return redirect("history")


def unsave_vacancy(request, vacancy_id: int):  # noqa: N802
    """Remove a vacancy from the user's saved list."""
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    try:
        saved_vacancy = Saved_vacancy.objects.get(user=user, id=vacancy_id)
        saved_vacancy.delete()
        messages.success(request, "Vacante eliminada de favoritos")
    except Saved_vacancy.DoesNotExist:
        messages.warning(request, "No has guardado esta vacante")
    return redirect("history")


def save_vacancy(request, vacancy_id: int):  # noqa: N802
    """Save a vacancy to the user's favourites."""
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    vacancy = Vacancy.objects.get(id=vacancy_id)
    if Saved_vacancy.objects.filter(user=user, vacancy=vacancy).exists():
        messages.warning(request, "Ya has guardado esta vacante")
    else:
        Saved_vacancy.objects.create(user=user, vacancy=vacancy)
        messages.success(request, "Vacante guardada con éxito")
    return redirect("feed")


def redirect_to_cv_inprover(request, vacancy_id: int, origin: str):  # noqa: N802
    """Redirect the user to upload a CV pre‑filled with the selected vacancy text."""
    if "user_id" not in request.session:
        return redirect("login")
    user = User.objects.get(id=request.session["user_id"])
    vacancy: Optional[Vacancy] = None
    if origin == "saved":
        saved_vacancy = Saved_vacancy.objects.filter(id=vacancy_id).first()
        if saved_vacancy:
            vacancy = Vacancy.objects.filter(id=saved_vacancy.vacancy.id).first()
    elif origin == "published":
        vacancy = Vacancy.objects.filter(id=vacancy_id).first()
    if not vacancy:
        messages.error(request, "No se encontró la vacante")
        return redirect("feed")
    if (
        Applied_resume.objects.filter(vacancy=vacancy, resume__uploaded_by=user).exists()
        and origin == "saved"
    ):
        messages.warning(request, "Ya has aplicado a esta vacante")
        return redirect("feed")
    return redirect(f"/upload_cv/?vacancy_id={vacancy.id}")


# ----- Helpers for generating responses -----
from docx import Document  # type: ignore
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib.units import inch  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore
from textwrap import wrap
from io import BytesIO


def _generate_docx_response(text: str) -> HttpResponse:
    doc = Document()
    doc.add_paragraph(text)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=mejorado_cv.docx"},
    )


def _generate_pdf_response(text: str) -> HttpResponse:
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch
    left_margin = inch
    right_margin = width - inch
    max_width = right_margin - left_margin
    lines = text.splitlines()
    for line in lines:
        # Basic markdown‑like styling
        if line.startswith("# "):
            p.setFont("Helvetica-Bold", 14)
            line = line[2:]
            y -= 20
        elif line.startswith("## "):
            p.setFont("Helvetica-Bold", 12)
            line = line[3:]
            y -= 15
        elif line.startswith("- "):
            p.setFont("Helvetica", 12)
            line = f"• {line[2:]}"
        elif "**" in line:
            p.setFont("Helvetica-Bold", 12)
            line = line.replace("**", "")
        else:
            p.setFont("Helvetica", 12)
        if y <= inch:
            p.showPage()
            p.setFont("Helvetica", 12)
            y = height - inch
        for l in wrap(line, width=int(max_width / 6)):
            if y <= inch:
                p.showPage()
                p.setFont("Helvetica", 12)
                y = height - inch
            p.drawString(left_margin, y, l)
            y -= 14
    p.save()
    buffer.seek(0)
    return HttpResponse(
        buffer,
        content_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=mejorado_cv.pdf"},
    )


def _generate_txt_response(text: str) -> HttpResponse:
    buffer = BytesIO()
    buffer.write(text.encode("utf-8"))
    buffer.seek(0)
    return HttpResponse(
        buffer,
        content_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=mejorado_cv.txt"},
    )