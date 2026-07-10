from __future__ import annotations

from typing import Any

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Entry
from .rules import (
    MAX_GUEST_STAY_LENGTH_DAYS,
    guest_stay_lengths,
    is_valid_guest_stay_length,
)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(
        self,
        attrs: dict[str, Any] | None = None,
    ) -> None:
        default_attrs = {
            "accept": "image/*",
        }

        super().__init__(
            {
                **default_attrs,
                **(attrs or {}),
            }
        )


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(
        self,
        data: Any,
        initial: Any = None,
    ) -> list[UploadedFile]:
        if not data:
            return []

        images = data if isinstance(data, (list, tuple)) else [data]

        # Bind the parent method outside the comprehension. Comprehensions
        # have their own execution scope, which makes zero-argument super()
        # fragile inside them.
        clean_image = super().clean

        return [
            clean_image(image, initial)
            for image in images
        ]


def stay_length_choices() -> list[tuple[int, str]]:
    choices: list[tuple[int, str]] = []

    for days in guest_stay_lengths():
        if days == 1:
            label = _("Idag")
        else:
            label = _("%(days)s dagar") % {
                "days": days,
            }

        choices.append((days, label))

    return choices


class BaseEntryCreateForm(forms.Form):
    """
    Shared input fields for all guestbook-entry creation flows.

    This form is intended for inheritance, not direct use.
    """

    title = forms.CharField(
        label=_("Rubrik"),
        max_length=160,
        widget=forms.TextInput(
            attrs={
                "placeholder": _(
                    "T.ex. Första grillningen på nya grillen"
                ),
            }
        ),
    )

    content = forms.CharField(
        label=_("Berättelse"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": _(
                    "Skriv några rader om besöket, vad som hände "
                    "och vilka som var med..."
                ),
            }
        ),
    )

    images = MultipleImageField(
        label=_("Bilder från dagen"),
        required=False,
    )


class GuestEntryCreateForm(BaseEntryCreateForm):
    """Input contract for unauthenticated guest entries."""

    field_order = [
        "guest_name",
        "title",
        "content",
        "stay_length_days",
        "images",
    ]

    guest_name = forms.CharField(
        label=_("Ditt namn"),
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("T.ex. Anna Larsson"),
            }
        ),
    )

    stay_length_days = forms.TypedChoiceField(
        label=_("Besöket gäller"),
        choices=stay_length_choices,
        initial=1,
        coerce=int,
    )

    def clean_guest_name(self) -> str:
        guest_name = self.cleaned_data["guest_name"].strip()

        if not guest_name:
            raise forms.ValidationError(
                _("Skriv ditt namn.")
            )

        return guest_name

    def clean_stay_length_days(self) -> int:
        days = self.cleaned_data["stay_length_days"]

        if not is_valid_guest_stay_length(days):
            raise forms.ValidationError(
                _(
                    "Anonyma inlägg kan bara gälla "
                    "de senaste %(days)s dagarna."
                )
                % {
                    "days": MAX_GUEST_STAY_LENGTH_DAYS,
                }
            )

        return days


class AuthenticatedEntryCreateForm(BaseEntryCreateForm):
    """Input contract for authenticated guestbook entries."""

    field_order = [
        "title",
        "content",
        "start_date",
        "end_date",
        "visibility",
        "images",
    ]

    start_date = forms.DateField(
        label=_("Från"),
        initial=timezone.localdate,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    end_date = forms.DateField(
        label=_("Till"),
        initial=timezone.localdate,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    visibility = forms.ChoiceField(
        label=_("Synlighet"),
        choices=Entry.Visibility.choices,
        initial=Entry.Visibility.PUBLIC,
        widget=forms.RadioSelect,
    )

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        maximum_date = timezone.localdate().isoformat()

        self.fields["start_date"].widget.attrs["max"] = maximum_date
        self.fields["end_date"].widget.attrs["max"] = maximum_date

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        today = timezone.localdate()

        if start_date is not None and start_date > today:
            self.add_error(
                "start_date",
                _("Startdatum kan inte vara i framtiden."),
            )

        if end_date is not None and end_date > today:
            self.add_error(
                "end_date",
                _("Slutdatum kan inte vara i framtiden."),
            )

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            self.add_error(
                "end_date",
                _("Slutdatum kan inte vara före startdatum."),
            )

        return cleaned_data
