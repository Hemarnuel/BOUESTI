from django import forms

from .models import Application, Interview, Job


class BootstrapModelForm(forms.ModelForm):
    """Adds Bootstrap 5 form-control classes automatically to every field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            if isinstance(field.widget, (forms.CheckboxInput,)):
                field.widget.attrs["class"] = (existing + " form-check-input").strip()
            else:
                field.widget.attrs["class"] = (existing + " form-control").strip()


class JobForm(BootstrapModelForm):
    class Meta:
        model = Job
        fields = [
            "title", "department", "location", "job_type",
            "description", "requirements", "salary_range", "status", "deadline",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "requirements": forms.Textarea(attrs={"rows": 4}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }


class JobSearchForm(forms.Form):
    """Implements 3.3.1: 'search and view available job opportunities using different search criteria'."""

    keyword = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Job title or keyword"}))
    department = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Department"}))
    location = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Location"}))
    job_type = forms.ChoiceField(
        required=False,
        choices=[("", "Any Job Type")] + list(Job.JobType.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class ApplicationForm(BootstrapModelForm):
    class Meta:
        model = Application
        fields = ["cv", "cover_letter"]
        widgets = {
            "cover_letter": forms.Textarea(attrs={"rows": 6, "placeholder": "Tell us why you're a great fit..."}),
        }

    def clean_cv(self):
        cv = self.cleaned_data["cv"]
        allowed_extensions = (".pdf", ".doc", ".docx")
        if not str(cv.name).lower().endswith(allowed_extensions):
            raise forms.ValidationError("Please upload your CV as a PDF or Word document.")
        max_size_mb = 5
        if cv.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError(f"CV file is too large (max {max_size_mb}MB).")
        return cv


class InterviewForm(BootstrapModelForm):
    class Meta:
        model = Interview
        fields = ["scheduled_datetime", "mode", "location_or_link", "notes"]
        widgets = {
            "scheduled_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
