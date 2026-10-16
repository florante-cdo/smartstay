from datetime import timedelta

from django.utils import timezone

from core.limits import MAX_ONLINE_GROUP
from enquiries.forms import EnquiryForm

from .base import BaseCase


class GroupCap(BaseCase):
    def form(self, guests):
        today = timezone.localdate()
        return EnquiryForm({
            "guest_name": "Group Lead", "phone": "0712345678", "preferred_contact": "phone",
            "requested_check_in": today + timedelta(days=10),
            "requested_check_out": today + timedelta(days=12),
            "guest_count": guests, "message": "",
        })

    def test_group_at_the_limit_is_accepted(self):
        form = self.form(MAX_ONLINE_GROUP)
        self.assertTrue(form.is_valid(), form.errors)

    def test_bigger_group_is_asked_to_call(self):
        form = self.form(MAX_ONLINE_GROUP + 1)
        self.assertFalse(form.is_valid())
        self.assertIn("call or WhatsApp", " ".join(form.errors["guest_count"]))
