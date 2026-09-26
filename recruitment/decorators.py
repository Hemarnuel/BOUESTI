from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from accounts.models import User


def role_required(*roles):
    """
    Restricts a view to users whose `role` is in `roles`.
    Used throughout to enforce the boundaries between Administrator,
    Recruiter, and Job Applicant capabilities described in 3.3.1.
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if (
                request.user.is_recruiter_role()
                and request.user.recruiter_approval != User.RecruiterApproval.APPROVED
            ):
                messages.error(request, "Your recruiter account is awaiting administrator approval.")
                return redirect("recruitment:home")
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect("recruitment:dashboard")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
