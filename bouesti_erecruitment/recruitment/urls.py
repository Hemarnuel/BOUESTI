from django.urls import path

from . import views

app_name = "recruitment"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Jobs
    path("jobs/", views.job_list_view, name="job_list"),
    path("jobs/new/", views.job_create_view, name="job_create"),
    path("jobs/<int:pk>/", views.job_detail_view, name="job_detail"),
    path("jobs/<int:pk>/edit/", views.job_update_view, name="job_update"),
    path("jobs/<int:pk>/delete/", views.job_delete_view, name="job_delete"),
    path("jobs/<int:pk>/apply/", views.job_apply_view, name="job_apply"),
    path("jobs/<int:pk>/applications/", views.job_applications_view, name="job_applications"),

    # Applications
    path("applications/mine/", views.my_applications_view, name="my_applications"),
    path("applications/<int:pk>/", views.application_detail_view, name="application_detail"),
    path("applications/<int:pk>/status/", views.application_update_status_view, name="application_update_status"),
    path("applications/<int:pk>/interview/", views.interview_schedule_view, name="interview_schedule"),

    # Notifications
    path("notifications/", views.notifications_view, name="notifications"),

    # Admin
    path("admin-panel/users/", views.admin_user_list_view, name="admin_users"),
    path("admin-panel/users/<int:pk>/toggle/", views.admin_toggle_user_active_view, name="admin_toggle_user"),
    path("admin-panel/reports/", views.admin_reports_view, name="admin_reports"),
]
