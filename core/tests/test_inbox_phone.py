from django.test import SimpleTestCase

from core.templatetags.staff_extras import short_name

from .base import BaseCase


class ShortName(SimpleTestCase):
    def test_first_name_and_initial_of_the_second(self):
        self.assertEqual(short_name("David Ochieng"), "David O.")

    def test_only_the_second_name_is_used_when_there_are_three(self):
        self.assertEqual(short_name("Mary Wanjiru Kamau"), "Mary W.")

    def test_single_or_empty_names_are_left_alone(self):
        self.assertEqual(short_name("Cher"), "Cher")
        self.assertEqual(short_name("  "), "")
        self.assertEqual(short_name(None), "")


class InboxOnPhones(BaseCase):
    def setUp(self):
        self.client.force_login(self.reception)

    def test_inbox_keeps_its_own_columns_and_offers_the_short_name(self):
        self.make_enquiry(guest_name="David Ochieng")
        response = self.client.get("/staff/inbox/")
        self.assertContains(response, "data-keep-table")
        self.assertContains(response, "David O.")
        self.assertContains(response, "David Ochieng")

    def test_inbox_no_longer_has_the_phone_only_dates_line(self):
        self.make_enquiry()
        self.assertNotContains(self.client.get("/staff/inbox/"), "text-garden-900/70 md:hidden")

    def test_details_panel_is_grouped_and_has_tap_to_call(self):
        enquiry = self.make_enquiry(phone="0712345678")
        response = self.client.get(f"/staff/enquiries/{enquiry.pk}/quick/")
        for heading in ("Guest", "Stay", "Where it came from"):
            self.assertContains(response, f">{heading}</h3>")
        self.assertContains(response, 'href="tel:0712345678"')
        self.assertContains(response, "Open full details")
