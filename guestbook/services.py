from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

from django.contrib.auth.base_user import AbstractBaseUser
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from accounts.services import get_or_create_profile_for_user

from .models import Entry, EntryImage, Event
from .rules import (
    MAX_GUEST_STAY_LENGTH_DAYS,
    MIN_GUEST_STAY_LENGTH_DAYS,
    is_valid_guest_stay_length,
)


@transaction.atomic
def create_authenticated_entry(
    *,
    user: AbstractBaseUser,
    title: str,
    content: str,
    start_date: date,
    end_date: date,
    visibility: str,
    event: Event | None = None,
    images: Iterable[UploadedFile] = (),
) -> Entry:
    """
    Create an entry owned by an authenticated user's profile.

    This use case owns profile resolution and authenticated-entry
    domain invariants.
    """

    _validate_entry_dates(
        start_date=start_date,
        end_date=end_date,
    )

    _validate_visibility(visibility)

    profile = get_or_create_profile_for_user(user)

    return _create_entry(
        profile=profile,
        guest_name="",
        title=title,
        content=content,
        start_date=start_date,
        end_date=end_date,
        visibility=visibility,
        event=event,
        images=images,
    )


@transaction.atomic
def create_guest_entry(
    *,
    guest_name: str,
    title: str,
    content: str,
    stay_length_days: int,
    event: Event | None = None,
    images: Iterable[UploadedFile] = (),
) -> Entry:
    """
    Create a public guest entry for a recent stay.

    Guests provide a stay length instead of explicit dates. This use case
    converts that input into the date range stored on the entry.
    """

    normalized_guest_name = guest_name.strip()

    if not normalized_guest_name:
        raise ValueError(
            "guest_name must not be empty"
        )

    if not is_valid_guest_stay_length(stay_length_days):
        raise ValueError(
            "stay_length_days must be between "
            f"{MIN_GUEST_STAY_LENGTH_DAYS} and "
            f"{MAX_GUEST_STAY_LENGTH_DAYS}"
        )

    end_date = timezone.localdate()
    start_date = end_date - timedelta(
        days=stay_length_days - 1
    )

    return _create_entry(
        profile=None,
        guest_name=normalized_guest_name,
        title=title,
        content=content,
        start_date=start_date,
        end_date=end_date,
        visibility=Entry.Visibility.PUBLIC,
        event=event,
        images=images,
    )


def _create_entry(
    *,
    title: str,
    content: str,
    start_date: date,
    end_date: date,
    profile: Profile | None,
    guest_name: str,
    visibility: str,
    event: Event | None,
    images: Iterable[UploadedFile],
) -> Entry:
    """
    Persist an already-decided entry.

    This function owns storage mechanics, not actor-specific decisions.
    """

    entry = Entry.objects.create(
        author=profile,
        family=profile.family if profile is not None else None,
        guest_name=guest_name,
        event=event,
        title=title,
        content=content,
        start_date=start_date,
        end_date=end_date,
        visibility=visibility,
    )

    for position, image in enumerate(images):
        EntryImage.objects.create(
            entry=entry,
            image=image,
            position=position,
        )

    return entry


def _validate_entry_dates(
    *,
    start_date: date,
    end_date: date,
) -> None:
    today = timezone.localdate()

    if start_date > today:
        raise ValueError(
            "start_date must not be in the future"
        )

    if end_date > today:
        raise ValueError(
            "end_date must not be in the future"
        )

    if end_date < start_date:
        raise ValueError(
            "end_date must not be before start_date"
        )


def _validate_visibility(
    visibility: str,
) -> None:
    if visibility not in Entry.Visibility.values:
        raise ValueError(
            f"Unsupported entry visibility: {visibility!r}"
        )
