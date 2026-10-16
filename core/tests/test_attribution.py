from django.test import RequestFactory

from enquiries.forms import EnquiryForm
from enquiries.models import Enquiry
from enquiries.services import attribute, create_web_enquiry

from .base import BaseCase


class AttributionRules(BaseCase):
    def test_no_tags_is_direct(self):
        a = attribute()
        self.assertEqual((a["campaign"], a["source"], a["medium"]), (None, "direct", "direct"))

    def test_known_campaign_copies_source_and_medium_from_the_record(self):
        # Guest-supplied source/medium are ignored; the campaign record is the truth.
        a = attribute(utm_campaign="weekend_offer", utm_source="spoofed", utm_medium="spoofed")
        self.assertEqual(a["campaign"], self.campaign)
        self.assertEqual((a["source"], a["medium"]), ("instagram", "social"))

    def test_code_matching_ignores_case_and_spaces(self):
        self.assertEqual(attribute(utm_campaign="  Weekend_Offer ")["campaign"], self.campaign)

    def test_unrecognised_code_is_unknown_and_keeps_the_raw_value(self):
        a = attribute(utm_campaign="mystery_promo")
        self.assertIsNone(a["campaign"])
        self.assertEqual((a["source"], a["medium"]), ("unknown", "unknown"))
        self.assertEqual(a["campaign_raw"], "mystery_promo")

    def test_source_without_campaign_is_unknown_not_credited(self):
        a = attribute(utm_source="facebook")
        self.assertIsNone(a["campaign"])
        self.assertEqual(a["source"], "unknown")

    def test_paused_campaign_is_not_credited(self):
        self.campaign.is_active = False
        self.campaign.save()
        self.assertIsNone(attribute(utm_campaign="weekend_offer")["campaign"])

    def test_very_long_raw_value_is_truncated(self):
        self.assertLessEqual(len(attribute(utm_campaign="x" * 500)["campaign_raw"]), 120)


class WebEnquiryCreation(BaseCase):
    def form(self):
        from datetime import timedelta

        from django.utils import timezone

        today = timezone.localdate()
        return EnquiryForm({
            "guest_name": "Web Guest", "phone": "0712345678", "preferred_contact": "phone",
            "requested_check_in": today + timedelta(days=10),
            "requested_check_out": today + timedelta(days=12),
            "guest_count": 2, "room_type": self.room.pk, "message": "",
        })

    def test_web_enquiry_is_new_with_campaign_and_first_history_row(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)
        e = create_web_enquiry(form, {"utm_campaign": "weekend_offer"}, "/promo/")
        self.assertEqual(e.status, Enquiry.Status.NEW)
        self.assertEqual(e.campaign, self.campaign)
        self.assertEqual(e.entry_channel, Enquiry.EntryChannel.WEB_FORM)
        self.assertEqual(e.status_changes.count(), 1)
