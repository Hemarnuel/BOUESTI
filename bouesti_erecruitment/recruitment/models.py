from django.conf import settings
from django.db import models
from django.urls import reverse

User = settings.AUTH_USER_MODEL


class RecruiterProfile(models.Model):
    """Extra attributes for the Recruiter class (3.4.8 Class Diagram)."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="recruiter_profile")
    department = models.CharField(max_length=150, blank=True)
    designation = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"Recruiter: {self.user.get_full_name() or self.user.username}"


class ApplicantProfile(models.Model):
    """Extra attributes for the JobApplicant class (3.4.8 Class Diagram)."""

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Prefer not to say"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="applicant_profile")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    address = models.TextField(blank=True)
    qualification = models.CharField(max_length=200, blank=True, help_text="Highest qualification, e.g. B.Sc Computer Science")
    resume = models.FileField(upload_to="resumes/", blank=True, null=True, help_text="Default/standing CV (optional)")

    def __str__(self):
        return f"Applicant: {self.user.get_full_name() or self.user.username}"


class Job(models.Model):
    """
    The Job class (3.4.8): a vacancy published by a Recruiter.
    Implements 3.3.1: 'Enable recruiters to create, update, and delete job
    vacancies' and 'Allow job seekers to search and view available job
    opportunities using different search criteria.'
    """

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full-Time"
        PART_TIME = "part_time", "Part-Time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs_posted",
                                   limit_choices_to={"role": "recruiter"})
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=150)
    location = models.CharField(max_length=150)
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    description = models.TextField()
    requirements = models.TextField(help_text="Minimum qualifications, skills, experience required")
    salary_range = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("recruitment:job_detail", args=[self.pk])

    @property
    def is_open(self):
        from django.utils import timezone
        return self.status == self.Status.OPEN and self.deadline >= timezone.localdate()


class Application(models.Model):
    """
    The Application class (3.4.8): records every application submitted
    for a vacancy. Implements 3.3.1: 'Enable applicants to submit job
    applications electronically' and 'Allow applicants to upload
    supporting documents such as curriculum vitae (CV), cover letters,
    and other required credentials.'
    """

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        SHORTLISTED = "shortlisted", "Shortlisted"
        INTERVIEW_SCHEDULED = "interview_scheduled", "Interview Scheduled"
        REJECTED = "rejected", "Rejected"
        HIRED = "hired", "Hired"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications",
                                   limit_choices_to={"role": "applicant"})
    cv = models.FileField(upload_to="applications/cv/")
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.SUBMITTED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(fields=["job", "applicant"], name="one_application_per_job_per_applicant")
        ]

    def __str__(self):
        return f"{self.applicant} -> {self.job}"


class Interview(models.Model):
    """
    The Interview class (3.4.8): manages interview schedules for
    shortlisted applicants. Implements 3.3.1: 'Allow recruiters to
    schedule interviews and update applicants on the progress of their
    applications.'
    """

    class Mode(models.TextChoices):
        ONSITE = "onsite", "On-site"
        ONLINE = "online", "Online"
        PHONE = "phone", "Phone"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="interview")
    scheduled_datetime = models.DateTimeField()
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ONSITE)
    location_or_link = models.CharField(max_length=255, help_text="Venue address, or meeting link for online interviews")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interview for {self.application}"


class Notification(models.Model):
    """
    The Notification class (3.4.8): communicates recruitment updates to
    users. Implements 3.3.1: 'Generate notifications to inform users of
    important recruitment activities such as successful applications,
    interview invitations, or application status updates.'
    """

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, help_text="Relative URL to navigate to when clicked")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"To {self.recipient}: {self.message[:50]}"
