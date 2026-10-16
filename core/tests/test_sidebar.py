from .base import BaseCase


class Sidebar(BaseCase):
    def test_sidebar_has_a_collapse_toggle(self):
        self.client.force_login(self.reception)
        response = self.client.get("/staff/")
        self.assertContains(response, 'id="sb-toggle"')
        self.assertContains(response, 'id="staff-aside"')

    def test_campaign_link_is_manager_only(self):
        self.client.force_login(self.reception)
        self.assertNotContains(self.client.get("/staff/"), "Campaign links")
        self.client.force_login(self.manager)
        self.assertContains(self.client.get("/staff/"), "Campaign links")
