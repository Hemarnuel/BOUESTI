from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Gives the Administrator role (section 3.3.1: 'Enable the administrator
    to manage users, monitor recruitment activities, and maintain the
    overall security and integrity of the system') a proper interface for
    managing every account in the system.
    """

    list_display = ("username", "email", "first_name", "last_name", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Recruitment Role", {"fields": ("role", "phone_number")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Recruitment Role", {"fields": ("role", "phone_number", "email")}),
    )
