"""
Admin configuration for the accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile', {
            'fields': ('role', 'phone', 'avatar'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Profile', {
            'fields': ('email', 'first_name', 'last_name', 'role', 'phone'),
        }),
    )
