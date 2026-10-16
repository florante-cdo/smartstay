from datetime import timedelta

from django.utils import timezone

from enquiries.models import Enquiry
from enquiries.services import create_staff_enquiry

from .base import BaseCase


class StaffEnteredEnquiry(BaseCase):
    def data(self, **extra):
        today = timezone.localdate()
        data = dict(
            channel="phone", guest_name="Caller", phone="0712 345 678", preferred_contact="phone",
            requested_check_in=today + timedelta(days=5),
            requested_check_out=today + timedelta(days=7),
            guest_count=2, room_type=self.room, message="", campaign=None,
        )
        data.update(extra)
        return data

    def test_without_campaign_source_is_the_channel(self):
        e = create_staff_enquiry(self.reception, self.data(channel="walk_in"))
        self.assertEqual(e.source, "walk_in")
        self.assertIsNone(e.campaign)
        self.assertEqual(e.entry_channel, "walk_in")

    def test_starts_contacted_and_assigned_to_the_logger(self):
        e = create_staff_enquiry(self.reception, self.data())
        self.assertEqual(e.status, Enquiry.Status.CONTACTED)
        self.assertEqual(e.assigned_to, self.reception)

    def test_history_and_note_are_written(self):
        e = create_staff_enquiry(self.reception, self.data())
        self.assertEqual(e.status_changes.count(), 1)
        self.assertEqual(e.notes.count(), 1)

    def test_mentioned_campaign_gets_the_credit(self):
        e = create_staff_enquiry(self.reception, self.data(campaign=self.campaign))
        self.assertEqual(e.campaign, self.campaign)
        self.assertEqual(e.source, "instagram")
        self.assertEqual(e.medium, "social")

    def test_form_rejects_too_many_guests_for_room(self):
        self.client.force_login(self.reception)
        d = self.data(guest_count=4, room_type=self.room.pk)
        d["requested_check_in"] = d["requested_check_in"].isoformat()
        d["requested_check_out"] = d["requested_check_out"].isoformat()
        d.pop("campaign")
        response = self.client.post("/staff/enquiries/new/", d)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sleeps up to 2")
        self.assertEqual(Enquiry.objects.count(), 0)
