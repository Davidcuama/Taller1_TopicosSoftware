from django.db import models
from users.models import User
from offer.models import Vacancy
import numpy as np


def _default_embedding() -> bytes:
    """Generate a random vector of length 1536 and return as bytes.

    This helper function encapsulates the default embedding used when
    creating a resume without computing an embedding via OpenAI.  The
    original project used a similar function, but naming it with a
    leading underscore prevents Django from inadvertently creating
    migrations when the function signature changes.
    """

    default_arr = np.random.rand(1536)
    return default_arr.tobytes()


class Resume(models.Model):
    """A resume uploaded by a job seeker.

    The embedding field stores a binary representation of the embedding
    vector (1536 floats) for efficient storage in SQLite.
    """

    version = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    vacancy_text = models.CharField(max_length=1000)
    extracted_text = models.TextField()
    upgraded_cv = models.TextField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    embedding = models.BinaryField(default=_default_embedding)
    image = models.ImageField(upload_to="images/resumes/", blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class Applied_resume(models.Model):
    """Through model representing a resume applied to a vacancy."""

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    match_rate = models.FloatField()
    state = models.CharField(
        default="applied",
        max_length=20,
        choices=[("applied", "Applied"), ("interviewed", "Interviewed"), ("rejected", "Rejected")],
    )
    feedback = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.resume.name


class Saved_vacancy(models.Model):
    """A saved vacancy bookmarked by a job seeker."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username} - {self.vacancy.title}"