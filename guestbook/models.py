from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Entry(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", _("Alla")
        MEMBERS = "members", _("Bara inloggade")

    author = models.ForeignKey(
        "accounts.Profile",
        verbose_name=_("author"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entries",
    )

    guest_name = models.CharField(
        _("guest name"),
        max_length=120,
        blank=True,
    )

    family = models.ForeignKey(
        "accounts.Family",
        verbose_name=_("family"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entries",
    )

    event = models.ForeignKey(
        "guestbook.Event",
        verbose_name=_("event"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entries",
    )

    title = models.CharField(_("title"), max_length=160)
    content = models.TextField(_("content"), blank=True)

    start_date = models.DateField(
        _("start date"),
        default=timezone.localdate,
    )
    end_date = models.DateField(
        _("end date"),
        default=timezone.localdate,
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    visibility = models.CharField(
        _("visibility"),
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )

    class Meta:
        verbose_name = _("entry")
        verbose_name_plural = _("entries")
        ordering = ["-start_date", "-created_at"]

    @property
    def display_author(self) -> str:
        if self.author:
            return self.author.display_name

        return self.guest_name

    @property
    def is_public(self) -> bool:
        return self.visibility == self.Visibility.PUBLIC

    @property
    def is_single_day(self) -> bool:
        return self.start_date == self.end_date

    def __str__(self) -> str:
        return self.title


class EntryImage(models.Model):
    entry = models.ForeignKey(
        Entry,
        verbose_name=_("entry"),
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(_("image"), upload_to="guestbook/")
    caption = models.CharField(_("caption"), max_length=160, blank=True)

    uploaded_at = models.DateTimeField(_("uploaded at"), auto_now_add=True)

    class Meta:
        verbose_name = _("entry image")
        verbose_name_plural = _("entry images")

    def __str__(self) -> str:
        return self.caption or self.image.name


class Event(models.Model):
    name = models.CharField(_("name"), max_length=160)
    slug = models.SlugField(_("slug"), unique=True)

    start_date = models.DateField(_("start date"))
    end_date = models.DateField(_("end date"), null=True, blank=True)

    description = models.TextField(_("description"), blank=True)

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return self.name
