from datetime import date

from .base import BaseCase


class SidebarFooter(BaseCase):
    def setUp(self):
        self.client.force_login(self.reception)

    def test_overview_has_the_date_and_the_guest_page_link(self):
        response = self.client.get("/staff/")
        self.assertContains(response, "View guest page")
        self.assertContains(response, date.today().strftime("%B"))

    def test_sidebar_no_longer_carries_the_guest_link_or_the_long_notice(self):
        response = self.client.get("/staff/inbox/")
        self.assertNotContains(response, "Open the guest page")

    def test_sign_out_and_profile_are_still_there(self):
        response = self.client.get("/staff/inbox/")
        self.assertContains(response, 'title="Sign out"')
        self.assertContains(response, 'title="My profile"')
