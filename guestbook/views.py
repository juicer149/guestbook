from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from accounts.models import Family

from .forms import (
    AuthenticatedEntryCreateForm,
    GuestEntryCreateForm,
)
from .models import Event
from .selectors import (
    EntrySearchScope,
    current_active_event,
    filter_entries,
    normalize_search_scope,
    visible_entries_for_user,
)
from .services import (
    create_authenticated_entry,
    create_guest_entry,
)


# TODO: Paginate entries when the guestbook grows.
def index(request: HttpRequest) -> HttpResponse:
    search = request.GET.get("q", "").strip()

    search_scope = normalize_search_scope(
        request.GET.get(
            "scope",
            EntrySearchScope.ALL,
        )
    )

    date_value = request.GET.get("date", "").strip()
    event_slug = request.GET.get("event", "").strip()

    selected_date = (
        parse_date(date_value)
        if date_value
        else None
    )

    event = (
        get_object_or_404(
            Event,
            slug=event_slug,
        )
        if event_slug
        else None
    )

    entries = visible_entries_for_user(request.user)

    entries = filter_entries(
        entries,
        search=search,
        search_scope=search_scope,
        selected_date=selected_date,
        event=event,
    )

    has_filters = bool(
        search
        or selected_date
        or event
    )

    return render(
        request,
        "guestbook/index.html",
        {
            "entries": entries,
            "search": search,
            "search_scope": search_scope,
            "search_scopes": EntrySearchScope,
            "selected_date": selected_date,
            "date_value": date_value if selected_date else "",
            "event": event,
            "has_filters": has_filters,
        },
    )


def family_entries(
    request: HttpRequest,
    slug: str,
) -> HttpResponse:
    family = get_object_or_404(
        Family,
        slug=slug,
    )

    entries = visible_entries_for_user(
        request.user
    ).filter(
        family=family,
    )

    return render(
        request,
        "guestbook/family_entries.html",
        {
            "family": family,
            "entries": entries,
        },
    )


def create(request: HttpRequest) -> HttpResponse:
    is_authenticated = request.user.is_authenticated
    active_event = current_active_event()

    form_class = (
        AuthenticatedEntryCreateForm
        if is_authenticated
        else GuestEntryCreateForm
    )

    if request.method == "POST":
        form = form_class(
            request.POST,
            request.FILES,
        )
    else:
        form = form_class()

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data

        if is_authenticated:
            create_authenticated_entry(
                user=request.user,
                title=data["title"],
                content=data["content"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                visibility=data["visibility"],
                event=active_event,
                images=data["images"],
            )
        else:
            create_guest_entry(
                guest_name=data["guest_name"],
                title=data["title"],
                content=data["content"],
                stay_length_days=data["stay_length_days"],
                event=active_event,
                images=data["images"],
            )

        return redirect("guestbook:index")

    return render(
        request,
        "guestbook/create.html",
        {
            "form": form,
            "active_event": active_event,
        },
    )
