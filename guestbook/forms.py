from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Entry


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []

        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(MultipleImageField, self).clean(file, initial) for file in files]


def stay_length_choices() -> list[tuple[int, str]]:
    choices = [(1, _("Idag"))]

    for days in range(2, 15):
        choices.append((days, _("%(days)s dagar") % {"days": days}))

    return choices


class EntryCreateForm(forms.Form):
    guest_name = forms.CharField(
        label=_("Ditt namn"),
        max_length=120,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("T.ex. Anna Larsson"),
            }
        ),
    )

    title = forms.CharField(
        label=_("Rubrik"),
        max_length=160,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("T.ex. Första grillningen på nya grillen"),
            }
        ),
    )

    content = forms.CharField(
        label=_("Berättelse"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": _(
                    "Skriv några rader om besöket, vad som hände och vilka som var med..."
                ),
            }
        ),
    )

    stay_length_days = forms.ChoiceField(
        label=_("Besöket gäller"),
        choices=stay_length_choices,
        initial=1,
        required=True,
    )

    start_date = forms.DateField(
        label=_("Från"),
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    end_date = forms.DateField(
        label=_("Till"),
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    visibility = forms.ChoiceField(
        label=_("Synlighet"),
        choices=Entry.Visibility.choices,
        initial=Entry.Visibility.PUBLIC,
        required=True,
        widget=forms.RadioSelect,
    )

    images = MultipleImageField(
        label=_("Bilder från dagen"),
        required=False,
    )

    def __init__(
        self,
        *args,
        show_guest_name: bool = True,
        show_visibility: bool = False,
        use_stay_length: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.use_stay_length = use_stay_length

        today = timezone.localdate()

        self.fields["start_date"].widget.attrs["max"] = today.isoformat()
        self.fields["end_date"].widget.attrs["max"] = today.isoformat()

        if not show_guest_name:
            self.fields.pop("guest_name")

        if not show_visibility:
            self.fields.pop("visibility")

        if use_stay_length:
            self.fields.pop("start_date")
            self.fields.pop("end_date")
        else:
            self.fields.pop("stay_length_days")

    def clean_guest_name(self):
        guest_name = self.cleaned_data.get("guest_name", "").strip()

        if "guest_name" in self.fields and not guest_name:
            raise forms.ValidationError(_("Skriv ditt namn."))

        return guest_name

    def clean_stay_length_days(self):
        days = int(self.cleaned_data["stay_length_days"])

        if days < 1 or days > 14:
            raise forms.ValidationError(
                _("Anonyma inlägg kan bara gälla de senaste 14 dagarna.")
            )

        return days

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        today = timezone.localdate()

        if start_date and start_date > today:
            self.add_error("start_date", _("Startdatum kan inte vara i framtiden."))

        if end_date and end_date > today:
            self.add_error("end_date", _("Slutdatum kan inte vara i framtiden."))

        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", _("Slutdatum kan inte vara före startdatum."))

        return cleaned_data
