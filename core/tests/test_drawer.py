from .base import BaseCase


class PhoneDrawer(BaseCase):
    def setUp(self):
        self.client.force_login(self.reception)

    def test_hamburger_is_icon_only_and_labelled(self):
        response = self.client.get("/staff/")
        self.assertContains(response, 'id="sb-menu"')
        self.assertContains(response, 'aria-label="Open menu"')
        self.assertNotContains(response, ">\n        Menu\n")

    def test_drawer_has_a_backdrop_and_a_close_button(self):
        response = self.client.get("/staff/")
        self.assertContains(response, 'id="sb-backdrop"')
        self.assertContains(response, 'id="sb-close"')

    def test_sign_out_and_profile_live_inside_the_drawer(self):
        response = self.client.get("/staff/")
        self.assertContains(response, 'id="sb-footwrap"')
        self.assertContains(response, 'title="Sign out"')
