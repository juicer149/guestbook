from django.contrib import admin

from .models import Entry, EntryImage, Event


class EntryImageInline(admin.TabularInline):
    model = EntryImage
    extra = 1
    fields = [
        "position",
        "image",
        "caption",
        "uploaded_at",
    ]
    readonly_fields = [
        "uploaded_at",
    ]
    ordering = [
        "position",
        "id",
    ]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author",
        "guest_name",
        "family",
        "event",
        "start_date",
        "end_date",
        "visibility",
        "created_at",
    ]

    list_filter = [
        "family",
        "event",
        "start_date",
        "end_date",
        "visibility",
        "created_at",
    ]

    search_fields = [
        "title",
        "content",
        "author__display_name",
        "guest_name",
        "family__name",
        "event__name",
    ]

    inlines = [EntryImageInline]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "start_date",
        "end_date",
        "slug",
    ]

    search_fields = [
        "name",
        "slug",
        "description",
    ]
