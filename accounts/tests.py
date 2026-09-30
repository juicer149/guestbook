from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Profile
from .services import get_or_create_profile_for_user


class ProfileTests(TestCase):
    def test_new_user_gets_a_profile(self) -> None:
        user = get_user_model().objects.create_user(
            username="albin",
            password="not-used-in-tests",
        )

        self.assertEqual(user.profile.display_name, "albin")

    def test_get_or_create_reuses_existing_profile(self) -> None:
        user = get_user_model().objects.create_user(
            username="albin",
            password="not-used-in-tests",
        )

        profile = get_or_create_profile_for_user(user)

        self.assertEqual(profile, user.profile)
        self.assertEqual(Profile.objects.count(), 1)
