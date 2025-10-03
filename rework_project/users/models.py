from django.db import models


class User(models.Model):
    """Custom user model for the AI‑Need‑Job platform.

    The platform distinguishes between job seekers and recruiters via the
    ``role`` field.  Authentication is handled manually via session state,
    not via Django's built‑in auth system, as inherited from the original
    project.
    """

    ROLE_CHOICES = (
        ("jobseeker", "Job Seeker"),
        ("recruiter", "Recruiter"),
    )

    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    is_authenticated = models.BooleanField(default=False)
    linkedin_id = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self) -> str:
        return self.username