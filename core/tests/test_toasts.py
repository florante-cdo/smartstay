from .base import BaseCase


class Toasts(BaseCase):
    def test_success_message_renders_as_a_toast(self):
        self.client.force_login(self.reception)
        response = self.client.post("/staff/profile/", {
            "action": "details", "first_name": "Rita", "last_name": "",
            "email": "", "phone": "", "job_title": "",
        }, follow=True)
        self.assertContains(response, 'data-level="success"')
        self.assertContains(response, "Your details are saved.")

    def test_error_message_is_a_persistent_alert(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            f"/staff/team/{self.manager.pk}/", {"action": "deactivate"}, follow=True
        )
        self.assertContains(response, 'data-level="error"')
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, "cannot deactivate your own account")

    def test_no_toast_without_a_message(self):
        self.client.force_login(self.reception)
        response = self.client.get("/staff/")
        self.assertContains(response, 'id="toasts"')
        self.assertNotContains(response, 'data-level="')
