from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import Family

from .models import Entry, Event
from .rules import (
    MAX_GUEST_STAY_LENGTH_DAYS,
    MIN_GUEST_STAY_LENGTH_DAYS,
    is_valid_guest_stay_length,
)
from .selectors import (
    EntrySearchScope,
    current_active_event,
    filter_entries,
    visible_entries_for_user,
)
from .services import (
    create_authenticated_entry,
    create_guest_entry,
)


def make_image(name: str = "photo.jpg") -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", (40, 30), "white").save(buffer, format="JPEG")

    return SimpleUploadedFile(
        name=name,
        content=buffer.getvalue(),
        content_type="image/jpeg",
    )


def make_entry(**overrides) -> Entry:
    today = timezone.localdate()

    values = {
        "title": "Grillkväll",
        "content": "",
        "guest_name": "Anna",
        "start_date": today,
        "end_date": today,
        "visibility": Entry.Visibility.PUBLIC,
    }
    values.update(overrides)

    return Entry.objects.create(**values)


class MediaRootMixin:
    """Store uploaded files in a temporary directory during a test."""

    def setUp(self) -> None:
        super().setUp()

        media_directory = TemporaryDirectory()
        self.addCleanup(media_directory.cleanup)

        media_override = override_settings(
            MEDIA_ROOT=media_directory.name,
        )
        media_override.enable()
        self.addCleanup(media_override.disable)


class RulesTests(TestCase):
    def test_accepts_lengths_within_bounds(self) -> None:
        self.assertTrue(
            is_valid_guest_stay_length(MIN_GUEST_STAY_LENGTH_DAYS)
        )
        self.assertTrue(
            is_valid_guest_stay_length(MAX_GUEST_STAY_LENGTH_DAYS)
        )

    def test_rejects_lengths_outside_bounds(self) -> None:
        self.assertFalse(
            is_valid_guest_stay_length(MIN_GUEST_STAY_LENGTH_DAYS - 1)
        )
        self.assertFalse(
            is_valid_guest_stay_length(MAX_GUEST_STAY_LENGTH_DAYS + 1)
        )


class GuestEntryServiceTests(MediaRootMixin, TestCase):
    def test_stay_length_becomes_a_date_range_ending_today(self) -> None:
        entry = create_guest_entry(
            guest_name="Anna",
            title="Helg på landet",
            content="",
            stay_length_days=3,
        )

        today = timezone.localdate()

        self.assertEqual(entry.end_date, today)
        self.assertEqual(entry.start_date, today - timedelta(days=2))

    def test_guest_entries_are_always_public(self) -> None:
        entry = create_guest_entry(
            guest_name="Anna",
            title="Besök",
            content="",
            stay_length_days=1,
        )

        self.assertEqual(entry.visibility, Entry.Visibility.PUBLIC)
        self.assertIsNone(entry.author)

    def test_guest_name_is_stripped(self) -> None:
        entry = create_guest_entry(
            guest_name="  Anna  ",
            title="Besök",
            content="",
            stay_length_days=1,
        )

        self.assertEqual(entry.guest_name, "Anna")

    def test_rejects_blank_guest_name(self) -> None:
        with self.assertRaises(ValueError):
            create_guest_entry(
                guest_name="   ",
                title="Besök",
                content="",
                stay_length_days=1,
            )

    def test_rejects_stay_length_outside_bounds(self) -> None:
        with self.assertRaises(ValueError):
            create_guest_entry(
                guest_name="Anna",
                title="Besök",
                content="",
                stay_length_days=MAX_GUEST_STAY_LENGTH_DAYS + 1,
            )

    def test_images_keep_their_upload_order(self) -> None:
        entry = create_guest_entry(
            guest_name="Anna",
            title="Besök",
            content="",
            stay_length_days=1,
            images=[make_image("first.jpg"), make_image("second.jpg")],
        )

        images = list(entry.images.all())

        self.assertEqual([image.position for image in images], [0, 1])
        self.assertIn("first", images[0].image.name)


class AuthenticatedEntryServiceTests(MediaRootMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.family = Family.objects.create(
            name="Larsson",
            slug="larsson",
        )
        self.user = get_user_model().objects.create_user(
            username="albin",
            password="not-used-in-tests",
        )
        self.user.profile.family = self.family
        self.user.profile.save()

    def create(self, **overrides) -> Entry:
        today = timezone.localdate()

        values = {
            "user": self.user,
            "title": "Midsommar",
            "content": "",
            "start_date": today,
            "end_date": today,
            "visibility": Entry.Visibility.MEMBERS,
        }
        values.update(overrides)

        return create_authenticated_entry(**values)

    def test_entry_belongs_to_profile_and_family(self) -> None:
        entry = self.create()

        self.assertEqual(entry.author, self.user.profile)
        self.assertEqual(entry.family, self.family)
        self.assertEqual(entry.guest_name, "")

    def test_rejects_future_dates(self) -> None:
        tomorrow = timezone.localdate() + timedelta(days=1)

        with self.assertRaises(ValueError):
            self.create(start_date=tomorrow, end_date=tomorrow)

    def test_rejects_end_before_start(self) -> None:
        today = timezone.localdate()

        with self.assertRaises(ValueError):
            self.create(
                start_date=today,
                end_date=today - timedelta(days=1),
            )

    def test_rejects_unknown_visibility(self) -> None:
        with self.assertRaises(ValueError):
            self.create(visibility="secret")


class SelectorTests(TestCase):
    def setUp(self) -> None:
        self.public = make_entry(
            title="Kräftskiva",
            visibility=Entry.Visibility.PUBLIC,
        )
        self.members = make_entry(
            title="Släktmöte",
            visibility=Entry.Visibility.MEMBERS,
        )

    def test_anonymous_users_see_public_entries_only(self) -> None:
        entries = visible_entries_for_user(AnonymousUser())

        self.assertEqual(list(entries), [self.public])

    def test_members_see_all_entries(self) -> None:
        user = get_user_model().objects.create_user(
            username="member",
            password="not-used-in-tests",
        )

        entries = visible_entries_for_user(user)

        self.assertCountEqual(entries, [self.public, self.members])

    def test_person_search_matches_guest_name(self) -> None:
        make_entry(title="Bad", guest_name="Kalle Karlsson")

        entries = filter_entries(
            Entry.objects.all(),
            search="kalle",
            search_scope=EntrySearchScope.PERSON,
        )

        self.assertEqual(
            [entry.title for entry in entries],
            ["Bad"],
        )

    def test_unknown_search_scope_falls_back_to_all(self) -> None:
        entries = filter_entries(
            Entry.objects.all(),
            search="kräft",
            search_scope="nonsense",
        )

        self.assertEqual(list(entries), [self.public])

    def test_date_filter_includes_every_day_of_a_stay(self) -> None:
        today = timezone.localdate()
        stay = make_entry(
            title="Veckan",
            start_date=today - timedelta(days=6),
            end_date=today,
        )

        entries = filter_entries(
            Entry.objects.all(),
            selected_date=today - timedelta(days=3),
        )

        self.assertEqual(list(entries), [stay])

    def test_current_active_event_covers_today(self) -> None:
        today = timezone.localdate()
        event = Event.objects.create(
            name="Sommar",
            slug="sommar",
            start_date=today - timedelta(days=5),
            end_date=today + timedelta(days=5),
        )
        Event.objects.create(
            name="Förra året",
            slug="forra-aret",
            start_date=today - timedelta(days=400),
            end_date=today - timedelta(days=300),
        )

        self.assertEqual(current_active_event(), event)


class ViewTests(MediaRootMixin, TestCase):
    def test_index_hides_member_entries_from_anonymous_visitors(self) -> None:
        make_entry(title="Offentligt", visibility=Entry.Visibility.PUBLIC)
        make_entry(title="Hemligt", visibility=Entry.Visibility.MEMBERS)

        response = self.client.get(reverse("guestbook:index"))

        self.assertContains(response, "Offentligt")
        self.assertNotContains(response, "Hemligt")

    def test_guest_can_create_an_entry(self) -> None:
        response = self.client.post(
            reverse("guestbook:create"),
            {
                "guest_name": "Anna",
                "title": "Tack för i helgen",
                "content": "Underbart väder.",
                "stay_length_days": "2",
                "images": [make_image()],
            },
        )

        self.assertRedirects(response, reverse("guestbook:index"))

        entry = Entry.objects.get()

        self.assertEqual(entry.guest_name, "Anna")
        self.assertEqual(entry.images.count(), 1)

    def test_invalid_guest_entry_is_not_saved(self) -> None:
        response = self.client.post(
            reverse("guestbook:create"),
            {
                "guest_name": "",
                "title": "Utan namn",
                "stay_length_days": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Entry.objects.exists())

    def test_unknown_family_returns_404(self) -> None:
        response = self.client.get(
            reverse(
                "guestbook:family_entries",
                kwargs={"slug": "finns-inte"},
            )
        )

        self.assertEqual(response.status_code, 404)
