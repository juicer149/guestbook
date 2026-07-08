from datetime import date
from typing import Iterable

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from accounts.models import Profile

from .models import Entry, EntryImage, Event


@transaction.atomic
def create_entry(
    *,
    title: str,
    content: str,
    start_date: date,
    end_date: date,
    profile: Profile | None = None,
    guest_name: str = "",
    visibility: str = Entry.Visibility.PUBLIC,
    event: Event | None = None,
    images: Iterable[UploadedFile] = (),
) -> Entry:
    entry = Entry.objects.create(
        author=profile,
        family=profile.family if profile else None,
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
