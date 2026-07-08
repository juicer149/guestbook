from datetime import date
from enum import StrEnum

from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import Entry, Event


class EntrySearchScope(StrEnum):
    ALL = "all"
    TITLE = "title"
    CONTENT = "content"
    PERSON = "person"
    FAMILY = "family"
    EVENT = "event"


def visible_entries_for_user(user) -> QuerySet[Entry]:
    entries = (
        Entry.objects
        .select_related("author", "family", "event")
        .prefetch_related("images")
    )

    if user.is_authenticated:
        return entries.filter(
            visibility__in=[
                Entry.Visibility.PUBLIC,
                Entry.Visibility.MEMBERS,
            ]
        )

    return entries.filter(visibility=Entry.Visibility.PUBLIC)


def normalize_search_scope(scope: str | EntrySearchScope) -> EntrySearchScope:
    try:
        return EntrySearchScope(scope)
    except ValueError:
        return EntrySearchScope.ALL


def search_filter_for(scope: str | EntrySearchScope, search: str) -> Q:
    normalized_scope = normalize_search_scope(scope)

    match normalized_scope:
        case EntrySearchScope.TITLE:
            return Q(title__icontains=search)

        case EntrySearchScope.CONTENT:
            return Q(content__icontains=search)

        case EntrySearchScope.PERSON:
            return (
                Q(guest_name__icontains=search)
                | Q(author__display_name__icontains=search)
            )

        case EntrySearchScope.FAMILY:
            return Q(family__name__icontains=search)

        case EntrySearchScope.EVENT:
            return Q(event__name__icontains=search)

        case EntrySearchScope.ALL:
            return (
                Q(title__icontains=search)
                | Q(content__icontains=search)
                | Q(guest_name__icontains=search)
                | Q(author__display_name__icontains=search)
                | Q(family__name__icontains=search)
                | Q(event__name__icontains=search)
            )


def filter_entries(
    entries: QuerySet[Entry],
    *,
    search: str = "",
    search_scope: str | EntrySearchScope = EntrySearchScope.ALL,
    selected_date: date | None = None,
    event: Event | None = None,
) -> QuerySet[Entry]:
    search = search.strip()

    if search:
        entries = entries.filter(search_filter_for(search_scope, search))

    if selected_date:
        entries = entries.filter(
            start_date__lte=selected_date,
            end_date__gte=selected_date,
        )

    if event:
        entries = entries.filter(event=event)

    return entries


def active_events_for_date(day: date) -> QuerySet[Event]:
    return Event.objects.filter(
        start_date__lte=day,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=day)
    )


def current_active_event() -> Event | None:
    return (
        active_events_for_date(timezone.localdate())
        .order_by("-start_date")
        .first()
    )


def events_for_archive() -> QuerySet[Event]:
    return Event.objects.order_by("-start_date")
