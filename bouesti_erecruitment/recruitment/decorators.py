from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


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
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect("recruitment:dashboard")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
