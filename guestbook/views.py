from datetime import date, timedelta

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.models import Family
from accounts.services import get_or_create_profile_for_user

from .forms import EntryCreateForm
from .models import Entry
from .services import create_entry


def visible_entries_for_user(user) -> QuerySet[Entry]:
    entries = (
        Entry.objects
        .select_related("author", "family")
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


def filter_entries(
    entries: QuerySet[Entry],
    *,
    query: str = "",
    selected_date: date | None = None,
) -> QuerySet[Entry]:
    query = query.strip()

    if query:
        entries = entries.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(guest_name__icontains=query)
            | Q(author__display_name__icontains=query)
            | Q(family__name__icontains=query)
        )

    if selected_date:
        entries = entries.filter(
            start_date__lte=selected_date,
            end_date__gte=selected_date,
        )

    return entries


# TODO: Paginate entries when the guestbook grows.
def index(request):
    query = request.GET.get("q", "").strip()
    date_value = request.GET.get("date", "").strip()
    selected_date = parse_date(date_value) if date_value else None

    entries = visible_entries_for_user(request.user)
    entries = filter_entries(
        entries,
        query=query,
        selected_date=selected_date,
    )

    has_filters = bool(query or selected_date)

    return render(
        request,
        "guestbook/index.html",
        {
            "entries": entries,
            "query": query,
            "selected_date": selected_date,
            "date_value": date_value if selected_date else "",
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
                images=form.cleaned_data["images"],
            )

            return redirect("guestbook:index")
    else:
        form = EntryCreateForm(**form_kwargs)

    return render(
        request,
        "guestbook/create.html",
        {"form": form},
    )
