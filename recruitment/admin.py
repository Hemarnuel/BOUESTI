from django.contrib import admin

from .models import Application, ApplicantProfile, Interview, Job, Notification, RecruiterProfile


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "location", "job_type", "status", "deadline", "posted_by")
    list_filter = ("status", "job_type", "department")
    search_fields = ("title", "department", "location")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "applied_at")
    list_filter = ("status",)
    search_fields = ("job__title", "applicant__username", "applicant__email")


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("application", "scheduled_datetime", "mode", "status")
    list_filter = ("mode", "status")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "message", "is_read", "created_at")
    list_filter = ("is_read",)


admin.site.register(RecruiterProfile)
admin.site.register(ApplicantProfile)
