from .base import BaseCase


class StaffAccess(BaseCase):
    def test_anonymous_is_sent_to_login(self):
        for url in ("/staff/", "/staff/inbox/", "/staff/campaigns/", "/staff/reservations/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn("login", response["Location"], url)

    def test_reception_can_work_enquiries(self):
        self.client.force_login(self.reception)
        for url in ("/staff/", "/staff/inbox/", "/staff/reservations/", "/staff/enquiries/new/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_reception_cannot_manage_campaigns(self):
        self.client.force_login(self.reception)
        for url in ("/staff/campaigns/", "/staff/campaigns/new/"):
            self.assertNotEqual(self.client.get(url).status_code, 200, url)

    def test_manager_can_manage_campaigns(self):
        self.client.force_login(self.manager)
        for url in ("/staff/campaigns/", "/staff/campaigns/new/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_reception_does_not_see_performance_tab(self):
        self.client.force_login(self.reception)
        self.assertNotContains(self.client.get("/staff/"), "Campaign performance")

    def test_manager_sees_performance_tab(self):
        self.client.force_login(self.manager)
        self.assertContains(self.client.get("/staff/"), "Campaign performance")


class DashboardApi(BaseCase):
    url = "/api/v1/dashboard/"

    def test_anonymous_is_refused(self):
        self.assertIn(self.client.get(self.url).status_code, (401, 403))

    def test_reception_is_refused(self):
        self.client.force_login(self.reception)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_manager_gets_json_with_expected_keys(self):
        self.make_enquiry(campaign=self.campaign, source="instagram", medium="social")
        self.client.force_login(self.manager)
        response = self.client.get(self.url + "?days=30")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        for key in ("kpis", "by_campaign", "funnel", "trend"):
            self.assertIn(key, body)
        self.assertEqual(body["kpis"]["enquiries"], 1)

    def test_pending_is_not_counted_as_confirmed(self):
        self.make_enquiry(status="reservation_pending")
        self.client.force_login(self.manager)
        body = self.client.get(self.url + "?days=all").json()
        self.assertEqual(body["kpis"]["confirmed"], 0)
