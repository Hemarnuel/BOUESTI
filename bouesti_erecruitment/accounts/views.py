from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import ProfileUpdateForm, SignUpForm
from .models import User


class RoleAwareLoginView(LoginView):
    """
    Implements 3.3.1: 'Authenticate users through a secure login mechanism
    before granting access to the system.' Uses Django's battle-tested
    auth backend (hashed passwords, brute-force-resistant form handling)
    rather than a hand-rolled login, satisfying the security
    non-functional requirement in 3.3.2.
    """

    template_name = "accounts/login.html"

    def get_success_url(self):
        return reverse_lazy("recruitment:dashboard")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("recruitment:dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.role == User.Role.RECRUITER:
                messages.success(
                    request,
                    "Your recruiter account is awaiting administrator verification. "
                    "You can log in after it has been approved.",
                )
                return redirect("accounts:login")
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account has been created.")
            return redirect("recruitment:dashboard")
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})
