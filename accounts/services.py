from django.contrib.auth import get_user_model

from .models import Profile


def get_or_create_profile_for_user(user: get_user_model()) -> Profile:
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={"display_name": user.get_username()},
    )
    return profile
