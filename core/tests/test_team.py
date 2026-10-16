from django.contrib.auth.models import User

from enquiries.models import Enquiry
from enquiries.services import staff_users

from .base import BaseCase

S = Enquiry.Status
NEW_MEMBER = {
    "first_name": "Amos", "last_name": "Kiprop", "username": "amos", "email": "amos@example.com",
    "phone": "0722 111 222", "job_title": "Night desk", "role": "reception",
    "password": "Gardens-Walk-47x",
}


class TeamAccess(BaseCase):
    def test_reception_cannot_open_the_staff_pages(self):
        self.client.force_login(self.reception)
        for url in ("/staff/team/", "/staff/team/new/", f"/staff/team/{self.manager.pk}/"):
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_manager_sees_the_list_and_the_sidebar_link(self):
        self.client.force_login(self.manager)
        response = self.client.get("/staff/team/")
        self.assertContains(response, "rita")
        self.assertContains(response, 'href="/staff/team/"')

    def test_reception_has_no_staff_link(self):
        self.client.force_login(self.reception)
        self.assertNotContains(self.client.get("/staff/"), 'href="/staff/team/"')


class AddStaff(BaseCase):
    def setUp(self):
        self.client.force_login(self.manager)

    def test_new_member_is_created_with_role_profile_and_can_sign_in(self):
        self.client.post("/staff/team/new/", NEW_MEMBER)
        user = User.objects.get(username="amos")
        self.assertTrue(user.groups.filter(name="Reception").exists())
        self.assertEqual(user.staff_profile.phone, "0722 111 222")
        self.client.logout()
        self.assertTrue(self.client.login(username="amos", password="Gardens-Walk-47x"))

    def test_duplicate_username_is_rejected(self):
        response = self.client.post("/staff/team/new/", {**NEW_MEMBER, "username": "RITA"})
        self.assertContains(response, "already taken")

    def test_weak_password_is_rejected(self):
        response = self.client.post("/staff/team/new/", {**NEW_MEMBER, "password": "12345678"})
        self.assertFalse(User.objects.filter(username="amos").exists())
        self.assertEqual(response.status_code, 200)


class DeactivateAndRoles(BaseCase):
    def setUp(self):
        self.client.force_login(self.manager)

    def post(self, user, **data):
        return self.client.post(f"/staff/team/{user.pk}/", data)

    def test_deactivating_blocks_sign_in_and_releases_open_enquiries(self):
        open_one = self.make_enquiry(status=S.CONTACTED, assigned_to=self.reception)
        done = self.make_enquiry(status=S.CONFIRMED, assigned_to=self.reception)
        self.post(self.reception, action="deactivate")
        self.reception.refresh_from_db()
        open_one.refresh_from_db()
        done.refresh_from_db()
        self.assertFalse(self.reception.is_active)
        self.assertIsNone(open_one.assigned_to)
        self.assertEqual(done.assigned_to, self.reception)
        self.assertFalse(self.client.login(username="rita", password="x"))

    def test_deactivated_person_is_not_offered_for_assignment(self):
        self.post(self.reception, action="deactivate")
        self.assertNotIn(self.reception, list(staff_users()))

    def test_reactivating_restores_sign_in(self):
        self.post(self.reception, action="deactivate")
        self.post(self.reception, action="reactivate")
        self.client.logout()
        self.assertTrue(self.client.login(username="rita", password="x"))

    def test_cannot_deactivate_yourself(self):
        self.post(self.manager, action="deactivate")
        self.manager.refresh_from_db()
        self.assertTrue(self.manager.is_active)

    def test_cannot_change_your_own_role(self):
        self.post(self.manager, action="role", role="reception")
        self.assertTrue(self.manager.groups.filter(name="Manager").exists())

    def test_last_active_manager_cannot_be_deactivated_by_another_manager(self):
        other = self._user("olive", "Manager")
        self.manager.is_active = False
        self.manager.save()
        self.client.force_login(other)
        self.post(other, action="deactivate")
        other.refresh_from_db()
        self.assertTrue(other.is_active)

    def test_role_can_be_changed_for_someone_else(self):
        self.post(self.reception, action="role", role="manager")
        self.assertTrue(self.reception.groups.filter(name="Manager").exists())
        self.assertFalse(self.reception.groups.filter(name="Reception").exists())

    def test_manager_can_set_a_new_password(self):
        self.post(self.reception, action="password",
                  new_password1="Gardens-Walk-47x", new_password2="Gardens-Walk-47x")
        self.reception.refresh_from_db()
        self.assertTrue(self.reception.check_password("Gardens-Walk-47x"))
