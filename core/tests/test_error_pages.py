from .base import BaseCase


class ErrorPages(BaseCase):
    def test_unknown_url_shows_branded_404(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_blocked_staff_page_is_branded_if_forbidden(self):
        self.client.force_login(self.reception)
        response = self.client.get("/staff/campaigns/")
        self.assertIn(response.status_code, (302, 403))
        if response.status_code == 403:
            self.assertTemplateUsed(response, "403.html")
