from datetime import timedelta

from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.models import Family
from accounts.services import get_or_create_profile_for_user

from .forms import EntryCreateForm
from .models import Entry, Event
from .selectors import (
    EntrySearchScope,
    current_active_event,
    filter_entries,
    normalize_search_scope,
    visible_entries_for_user,
)
from .services import create_entry


# TODO: Paginate entries when the guestbook grows.
def index(request):
    search = request.GET.get("q", "").strip()
    search_scope = request.GET.get("scope", EntrySearchScope.ALL)
    date_value = request.GET.get("date", "").strip()
    event_slug = request.GET.get("event", "").strip()

    selected_date = parse_date(date_value) if date_value else None
    event = get_object_or_404(Event, slug=event_slug) if event_slug else None

    entries = visible_entries_for_user(request.user)
    entries = filter_entries(
        entries,
        search=search,
        search_scope=search_scope,
        selected_date=selected_date,
        event=event,
    )

    has_filters = bool(search or selected_date or event)

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


def family_entries(request, slug):
    family = get_object_or_404(Family, slug=slug)
    entries = visible_entries_for_user(request.user).filter(family=family)

    return render(
        request,
        "guestbook/family_entries.html",
        {
            "family": family,
            "entries": entries,
        },
    )


def create(request):
    user_is_authenticated = request.user.is_authenticated
    active_event = current_active_event()

    form_kwargs = {
        "show_guest_name": not user_is_authenticated,
        "show_visibility": user_is_authenticated,
        "use_stay_length": not user_is_authenticated,
    }

    if request.method == "POST":
        form = EntryCreateForm(
            request.POST,
            request.FILES,
            **form_kwargs,
        )

        if form.is_valid():
            profile = None
            guest_name = ""
            visibility = Entry.Visibility.PUBLIC

            if user_is_authenticated:
                profile = get_or_create_profile_for_user(request.user)
                visibility = form.cleaned_data["visibility"]
                start_date = form.cleaned_data["start_date"]
                end_date = form.cleaned_data["end_date"]
            else:
                guest_name = form.cleaned_data["guest_name"]

                stay_length_days = form.cleaned_data["stay_length_days"]
                end_date = timezone.localdate()
                start_date = end_date - timedelta(days=stay_length_days - 1)

            create_entry(
                profile=profile,
                guest_name=guest_name,
                title=form.cleaned_data["title"],
                content=form.cleaned_data["content"],
                start_date=start_date,
                end_date=end_date,
                visibility=visibility,
                event=active_event,
                images=form.cleaned_data["images"],
            )

            return redirect("guestbook:index")
    else:
        form = EntryCreateForm(**form_kwargs)

    return render(
        request,
        "guestbook/create.html",
        {
            "form": form,
            "active_event": active_event,
        },
    )
