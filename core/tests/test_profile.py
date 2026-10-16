from core.models import StaffProfile

from .base import BaseCase


class ProfilePage(BaseCase):
    url = "/staff/profile/"

    def test_anonymous_is_sent_to_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_sidebar_links_to_the_profile(self):
        self.client.force_login(self.reception)
        self.assertContains(self.client.get("/staff/"), self.url)

    def test_details_are_saved_to_user_and_profile(self):
        self.client.force_login(self.reception)
        self.client.post(self.url, {
            "action": "details", "first_name": "Rita", "last_name": "Wanjiru",
            "email": "rita@example.com", "phone": "0712 345 678", "job_title": "Front desk",
        })
        self.reception.refresh_from_db()
        self.assertEqual(self.reception.first_name, "Rita")
        self.assertEqual(self.reception.email, "rita@example.com")
        profile = StaffProfile.objects.get(user=self.reception)
        self.assertEqual((profile.phone, profile.job_title), ("0712 345 678", "Front desk"))

    def test_bad_phone_is_rejected(self):
        self.client.force_login(self.reception)
        response = self.client.post(self.url, {"action": "details", "first_name": "Rita", "phone": "abc"})
        self.assertContains(response, "Enter a phone number")

    def test_password_change_works_and_keeps_you_signed_in(self):
        self.client.force_login(self.reception)
        self.client.post(self.url, {
            "action": "password", "old_password": "x",
            "new_password1": "Gardens-Walk-47x", "new_password2": "Gardens-Walk-47x",
        })
        self.reception.refresh_from_db()
        self.assertTrue(self.reception.check_password("Gardens-Walk-47x"))
        self.assertEqual(self.client.get("/staff/").status_code, 200)

    def test_wrong_old_password_changes_nothing(self):
        self.client.force_login(self.reception)
        self.client.post(self.url, {
            "action": "password", "old_password": "wrong",
            "new_password1": "Gardens-Walk-47x", "new_password2": "Gardens-Walk-47x",
        })
        self.reception.refresh_from_db()
        self.assertTrue(self.reception.check_password("x"))
