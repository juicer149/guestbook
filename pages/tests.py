from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_page_renders(self) -> None:
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
