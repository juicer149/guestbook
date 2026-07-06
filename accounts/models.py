from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Family(models.Model):
    name = models.CharField(_("name"), max_length=120)
    slug = models.SlugField(_("slug"), unique=True)

    parent = models.ForeignKey(
        "self",
        verbose_name=_("parent family"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="branches",
    )

    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("family")
        verbose_name_plural = _("families")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        related_name="profile",
    )

    display_name = models.CharField(_("display name"), max_length=120)

    family = models.ForeignKey(
        Family,
        verbose_name=_("family"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
    )

    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")
        ordering = ["display_name"]

    def __str__(self) -> str:
        return self.display_name
