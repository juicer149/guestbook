from django.contrib import admin

from .models import Family, Profile


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "slug"]
    list_filter = ["parent"]
    search_fields = ["name", "slug"]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["display_name", "user", "family"]
    list_filter = ["family"]
    search_fields = ["display_name", "user__username", "family__name"]
