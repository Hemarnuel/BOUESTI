from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Base User class for the E-Recruitment System.

    Mirrors the Class Diagram in Chapter 3 (section 3.4.8): the User class
    is the parent from which Administrator, Recruiter and JobApplicant
    derive their common attributes. Django's auth system is extended here
    with a 'role' field rather than three separate tables, which keeps a
    single authentication/login mechanism (as required in 3.3.1) while
    still letting the system tell the three user types apart.
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        RECRUITER = "recruiter", "Recruiter"
        APPLICANT = "applicant", "Job Applicant"

    class RecruiterApproval(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.APPLICANT)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    recruiter_approval = models.CharField(
        max_length=20,
        choices=RecruiterApproval.choices,
        default=RecruiterApproval.APPROVED,
    )
    recruiter_reviewed_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_recruiters",
    )
    recruiter_reviewed_at = models.DateTimeField(null=True, blank=True)

    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    def is_recruiter_role(self):
        return self.role == self.Role.RECRUITER

    def is_applicant_role(self):
        return self.role == self.Role.APPLICANT

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
