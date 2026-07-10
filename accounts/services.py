from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser

from .models import Profile


def get_or_create_profile_for_user(
    user: AbstractBaseUser,
) -> Profile:
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            "display_name": user.get_username(),
        },
    )

    return profile
