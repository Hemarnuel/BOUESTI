from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User

from .decorators import role_required
from .forms import ApplicationForm, InterviewForm, JobForm, JobSearchForm
from .models import Application, Interview, Job, Notification
from .utils import notify


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def home_view(request):
    """Public landing page listing the latest open vacancies."""
    latest_jobs = Job.objects.filter(status=Job.Status.OPEN, deadline__gte=timezone.localdate())[:6]
    return render(request, "recruitment/home.html", {"latest_jobs": latest_jobs})


def job_list_view(request):
    """Implements 3.3.1: search/view available jobs using different search criteria."""
    form = JobSearchForm(request.GET or None)
    jobs = Job.objects.filter(status=Job.Status.OPEN, deadline__gte=timezone.localdate())

    if form.is_valid():
        keyword = form.cleaned_data.get("keyword")
        department = form.cleaned_data.get("department")
        location = form.cleaned_data.get("location")
        job_type = form.cleaned_data.get("job_type")

        if keyword:
            jobs = jobs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword))
        if department:
            jobs = jobs.filter(department__icontains=department)
        if location:
            jobs = jobs.filter(location__icontains=location)
        if job_type:
            jobs = jobs.filter(job_type=job_type)

    paginator = Paginator(jobs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "recruitment/job_list.html", {"form": form, "page_obj": page_obj})


def job_detail_view(request, pk):
    job = get_object_or_404(Job, pk=pk)
    already_applied = False
    if request.user.is_authenticated and request.user.is_applicant_role():
        already_applied = Application.objects.filter(job=job, applicant=request.user).exists()
    return render(request, "recruitment/job_detail.html", {"job": job, "already_applied": already_applied})


# ---------------------------------------------------------------------------
# Dashboard router
# ---------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    user = request.user
    if user.is_admin_role():
        return admin_dashboard(request)
    if user.is_recruiter_role():
        if user.recruiter_approval != User.RecruiterApproval.APPROVED:
            messages.error(request, "Your recruiter account is awaiting administrator approval.")
            return redirect("recruitment:home")
        return recruiter_dashboard(request)
    return applicant_dashboard(request)


def applicant_dashboard(request):
    applications = Application.objects.filter(applicant=request.user).select_related("job")
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    context = {
        "applications": applications,
        "unread_count": unread_count,
        "stats": {
            "total": applications.count(),
            "shortlisted": applications.filter(status=Application.Status.SHORTLISTED).count(),
            "interviews": applications.filter(status=Application.Status.INTERVIEW_SCHEDULED).count(),
            "hired": applications.filter(status=Application.Status.HIRED).count(),
        },
    }
    return render(request, "recruitment/dashboard_applicant.html", context)


def recruiter_dashboard(request):
    jobs = Job.objects.filter(posted_by=request.user).annotate(application_count=Count("applications"))
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    context = {
        "jobs": jobs,
        "unread_count": unread_count,
        "stats": {
            "total_jobs": jobs.count(),
            "open_jobs": jobs.filter(status=Job.Status.OPEN).count(),
            "total_applications": Application.objects.filter(job__posted_by=request.user).count(),
        },
    }
    return render(request, "recruitment/dashboard_recruiter.html", context)


def admin_dashboard(request):
    """Implements 3.3.1: manage users, monitor recruitment activities, generate reports."""
    context = {
        "stats": {
            "total_users": User.objects.count(),
            "total_recruiters": User.objects.filter(role=User.Role.RECRUITER).count(),
            "pending_recruiters": User.objects.filter(
                role=User.Role.RECRUITER,
                recruiter_approval=User.RecruiterApproval.PENDING,
            ).count(),
            "total_applicants": User.objects.filter(role=User.Role.APPLICANT).count(),
            "total_jobs": Job.objects.count(),
            "open_jobs": Job.objects.filter(status=Job.Status.OPEN).count(),
            "total_applications": Application.objects.count(),
            "hired": Application.objects.filter(status=Application.Status.HIRED).count(),
        },
        "recent_users": User.objects.order_by("-created_at")[:8],
        "recent_jobs": Job.objects.order_by("-created_at")[:8],
    }
    return render(request, "recruitment/dashboard_admin.html", context)


# ---------------------------------------------------------------------------
# Recruiter: job management
# ---------------------------------------------------------------------------

@role_required(User.Role.RECRUITER)
def job_create_view(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            messages.success(request, "Job vacancy published successfully.")
            return redirect("recruitment:dashboard")
    else:
        form = JobForm()
    return render(request, "recruitment/job_form.html", {"form": form, "title": "Post a New Job"})


@role_required(User.Role.RECRUITER)
def job_update_view(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job vacancy updated successfully.")
            return redirect("recruitment:dashboard")
    else:
        form = JobForm(instance=job)
    return render(request, "recruitment/job_form.html", {"form": form, "title": "Edit Job Vacancy"})


@role_required(User.Role.RECRUITER)
def job_delete_view(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    if request.method == "POST":
        job.delete()
        messages.success(request, "Job vacancy deleted.")
        return redirect("recruitment:dashboard")
    return render(request, "recruitment/job_confirm_delete.html", {"job": job})


@role_required(User.Role.RECRUITER)
def job_applications_view(request, pk):
    """Recruiter reviews applications for one of their vacancies (3.3.1)."""
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    applications = job.applications.select_related("applicant").order_by("-applied_at")
    return render(request, "recruitment/job_applications.html", {"job": job, "applications": applications})


@role_required(User.Role.RECRUITER)
def application_update_status_view(request, pk):
    """Recruiter shortlists / rejects / hires a candidate; applicant is notified."""
    application = get_object_or_404(Application, pk=pk, job__posted_by=request.user)
    if request.method == "POST":
        new_status = request.POST.get("status")
        valid_statuses = dict(Application.Status.choices)
        if new_status in valid_statuses:
            application.status = new_status
            application.save()
            notify(
                application.applicant,
                f"Your application for '{application.job.title}' is now: {valid_statuses[new_status]}.",
                link=f"/applications/{application.pk}/",
            )
            messages.success(request, f"Application status updated to {valid_statuses[new_status]}.")
    return redirect("recruitment:job_applications", pk=application.job.pk)


@role_required(User.Role.RECRUITER)
def interview_schedule_view(request, pk):
    application = get_object_or_404(Application, pk=pk, job__posted_by=request.user)
    interview = getattr(application, "interview", None)

    if request.method == "POST":
        form = InterviewForm(request.POST, instance=interview)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.application = application
            interview.save()
            application.status = Application.Status.INTERVIEW_SCHEDULED
            application.save()
            notify(
                application.applicant,
                f"An interview has been scheduled for your application to '{application.job.title}'.",
                link=f"/applications/{application.pk}/",
            )
            messages.success(request, "Interview scheduled and applicant notified.")
            return redirect("recruitment:job_applications", pk=application.job.pk)
    else:
        form = InterviewForm(instance=interview)

    return render(request, "recruitment/interview_form.html", {"form": form, "application": application})


# ---------------------------------------------------------------------------
# Applicant: applying and tracking
# ---------------------------------------------------------------------------

@role_required(User.Role.APPLICANT)
def job_apply_view(request, pk):
    job = get_object_or_404(Job, pk=pk)

    if not job.is_open:
        messages.error(request, "This vacancy is no longer accepting applications.")
        return redirect("recruitment:job_detail", pk=pk)

    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You have already applied for this job.")
        return redirect("recruitment:job_detail", pk=pk)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            notify(
                job.posted_by,
                f"New application received for '{job.title}' from {request.user.get_full_name() or request.user.username}.",
                link=f"/jobs/{job.pk}/applications/",
            )
            messages.success(request, "Application submitted successfully. Good luck!")
            return redirect("recruitment:my_applications")
    else:
        form = ApplicationForm()

    return render(request, "recruitment/job_apply.html", {"form": form, "job": job})


@role_required(User.Role.APPLICANT)
def my_applications_view(request):
    applications = Application.objects.filter(applicant=request.user).select_related("job")
    return render(request, "recruitment/my_applications.html", {"applications": applications})


@login_required
def application_detail_view(request, pk):
    application = get_object_or_404(Application, pk=pk)
    user = request.user
    if not (user == application.applicant or user == application.job.posted_by or user.is_admin_role()):
        messages.error(request, "You do not have permission to view that application.")
        return redirect("recruitment:dashboard")
    return render(request, "recruitment/application_detail.html", {"application": application})


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "recruitment/notifications.html", {"notifications": notifications})


# ---------------------------------------------------------------------------
# Admin: user management & reports
# ---------------------------------------------------------------------------

@role_required(User.Role.ADMIN)
def admin_user_list_view(request):
    users = User.objects.all().order_by("-created_at")
    return render(request, "recruitment/admin_user_list.html", {"users": users})
    
def build_admin_context():
    return {
        "stats": {
            "total_users": User.objects.count(),
            "total_recruiters": User.objects.filter(role=User.Role.RECRUITER).count(),
            "approved_recruiters": User.objects.filter(
                role=User.Role.RECRUITER,
                recruiter_approval=User.RecruiterApproval.APPROVED,
            ).count(),
            "pending_recruiters": User.objects.filter(
                role=User.Role.RECRUITER,
                recruiter_approval=User.RecruiterApproval.PENDING,
            ).count(),
            "total_applicants": User.objects.filter(role=User.Role.APPLICANT).count(),
            "total_jobs": Job.objects.count(),
            "open_jobs": Job.objects.filter(status=Job.Status.OPEN).count(),
            "total_applications": Application.objects.count(),
            "hired": Application.objects.filter(status=Application.Status.HIRED).count(),
        },
        "recent_users": User.objects.order_by("-created_at")[:8],
        "recent_jobs": Job.objects.order_by("-created_at")[:8],
    }


def admin_dashboard(request):
    """Implements 3.3.1: manage users, monitor recruitment activities, generate reports."""
    return render(request, "recruitment/dashboard_admin.html", build_admin_context())


@role_required(User.Role.ADMIN)
def super_admin_dashboard(request):
    """Dedicated dashboard for the super admin with a full operational overview."""
    context = build_admin_context()
    context["stats"]["is_super_admin"] = True
    return render(request, "recruitment/dashboard_super_admin.html", context)


@role_required(User.Role.ADMIN)
def admin_toggle_user_active_view(request, pk):
    target = get_object_or_404(User, pk=pk)
    if request.method == "POST" and target != request.user:
        if (
            target.role == User.Role.RECRUITER
            and target.recruiter_approval != User.RecruiterApproval.APPROVED
            and not target.is_active
        ):
            messages.error(request, "A recruiter must be approved before their account can be activated.")
            return redirect("recruitment:admin_users")
        target.is_active = not target.is_active
        target.save()
        messages.success(request, f"{target.username} is now {'active' if target.is_active else 'deactivated'}.")
    return redirect("recruitment:admin_users")


@role_required(User.Role.ADMIN)
def admin_recruiter_approvals_view(request):
    pending_recruiters = User.objects.filter(
        role=User.Role.RECRUITER,
        recruiter_approval=User.RecruiterApproval.PENDING,
    ).order_by("created_at")
    return render(
        request,
        "recruitment/admin_recruiter_approvals.html",
        {"pending_recruiters": pending_recruiters},
    )


@role_required(User.Role.ADMIN)
@require_POST
def admin_review_recruiter_view(request, pk):
    recruiter = get_object_or_404(
        User,
        pk=pk,
        role=User.Role.RECRUITER,
        recruiter_approval=User.RecruiterApproval.PENDING,
    )
    decision = request.POST.get("decision")
    if decision not in (User.RecruiterApproval.APPROVED, User.RecruiterApproval.REJECTED):
        messages.error(request, "Choose approve or reject to complete the review.")
        return redirect("recruitment:admin_recruiter_approvals")

    recruiter.recruiter_approval = decision
    recruiter.recruiter_reviewed_by = request.user
    recruiter.recruiter_reviewed_at = timezone.now()
    recruiter.is_active = decision == User.RecruiterApproval.APPROVED
    recruiter.save(
        update_fields=[
            "recruiter_approval",
            "recruiter_reviewed_by",
            "recruiter_reviewed_at",
            "is_active",
        ]
    )
    verb = "approved" if decision == User.RecruiterApproval.APPROVED else "rejected"
    messages.success(request, f"Recruiter account for {recruiter.username} was {verb}.")
    return redirect("recruitment:admin_recruiter_approvals")


@role_required(User.Role.ADMIN)
def admin_reports_view(request):
    """Implements 3.3.1: 'Generate recruitment reports ... supporting decision-making.'"""
    jobs_by_department = (
        Job.objects.values("department").annotate(total=Count("id")).order_by("-total")
    )
    applications_by_status = (
        Application.objects.values("status").annotate(total=Count("id")).order_by("-total")
    )
    top_jobs = (
        Job.objects.annotate(application_count=Count("applications"))
        .order_by("-application_count")[:10]
    )
    context = {
        "jobs_by_department": jobs_by_department,
        "applications_by_status": applications_by_status,
        "top_jobs": top_jobs,
    }
    return render(request, "recruitment/admin_reports.html", context)
