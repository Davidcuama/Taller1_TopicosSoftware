from django.db import models
import numpy as np


def _default_embedding() -> bytes:
    """Generate a random vector of length 1536 and return as bytes."""
    return np.random.rand(1536).tobytes()


class Vacancy(models.Model):
    """A job vacancy posted by a recruiter."""

    title = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField(null=True, blank=True)
    state = models.CharField(
        default="open", max_length=20, choices=[("open", "Open"), ("closed", "Closed")]
    )
    uploaded_by = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="vacancies"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    embedding = models.BinaryField(default=_default_embedding)

    def __str__(self) -> str:
        return self.title