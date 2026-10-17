from .base import BaseCase


class MobileLayout(BaseCase):
    def test_staff_pages_have_a_menu_button_for_phones(self):
        self.client.force_login(self.reception)
        for url in ("/staff/", "/staff/inbox/", "/staff/reservations/"):
            response = self.client.get(url)
            self.assertContains(response, 'id="sb-menu"', msg_prefix=url)
            self.assertContains(response, 'id="sb-nav"', msg_prefix=url)

    def test_every_page_declares_the_viewport(self):
        self.client.force_login(self.manager)
        for url in ("/promo/", "/staff/", "/staff/team/", "/staff/campaigns/", "/staff/profile/"):
            self.assertContains(
                self.client.get(url), 'name="viewport" content="width=device-width, initial-scale=1"',
                msg_prefix=url,
            )

    def test_tables_have_headings_the_card_layout_can_use(self):
        self.client.force_login(self.manager)
        response = self.client.get("/staff/team/")
        self.assertContains(response, "<thead")
        self.assertContains(response, "Open enquiries")
