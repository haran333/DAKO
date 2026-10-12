from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["email", "first_name", "supabase_id", "is_staff", "date_joined"]
    fieldsets = UserAdmin.fieldsets + (("Supabase", {"fields": ("supabase_id", "avatar_url")}),)
