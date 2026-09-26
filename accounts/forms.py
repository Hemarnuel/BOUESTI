from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    """
    Implements 3.3.1: 'Allow administrators, recruiters, and job applicants
    to register and create user accounts.'

    Administrators are not self-registered through this public form for
    security reasons (an open door to admin accounts would violate the
    non-functional security requirement in 3.3.2); admin accounts are
    created via Django's createsuperuser command or by an existing
    administrator. The public form lets a visitor sign up as either a
    Recruiter or a Job Applicant.
    """

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(
        choices=[
            (User.Role.APPLICANT, "Job Applicant"),
            (User.Role.RECRUITER, "Recruiter"),
        ],
        widget=forms.RadioSelect,
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "phone_number", "role", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "role":
                field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.phone_number = self.cleaned_data.get("phone_number", "")
        user.role = self.cleaned_data["role"]
        if user.role == User.Role.RECRUITER:
            user.recruiter_approval = User.RecruiterApproval.PENDING
            user.is_active = False
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }
