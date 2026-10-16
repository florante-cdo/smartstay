from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone

from campaigns.models import Campaign
from enquiries.models import Enquiry

from .base import BaseCase


class ResetDemo(BaseCase):
    def run_reset(self, **kwargs):
        call_command("reset_demo", stdout=StringIO(), **kwargs)

    @override_settings(DEMO_MODE=False)
    def test_refuses_when_demo_mode_is_off(self):
        with self.assertRaises(CommandError):
            self.run_reset(yes=True)

    @override_settings(DEMO_MODE=True)
    def test_refuses_without_confirmation(self):
        with self.assertRaises(CommandError):
            self.run_reset()

    @override_settings(DEMO_MODE=True)
    def test_removes_demo_leftovers_and_restores_campaigns(self):
        leftover = self.make_enquiry(guest_name="Left over from a test run")
        stale = Campaign.objects.create(
            name="Stale test campaign", code="stale_test", source="tiktok", medium="organic_social"
        )
        self.campaign.ends_on = timezone.localdate() - timedelta(days=3)
        self.campaign.is_active = False
        self.campaign.save()

        self.run_reset(yes=True, count=10)

        self.assertFalse(Enquiry.objects.filter(pk=leftover.pk).exists())
        self.assertFalse(Campaign.objects.filter(pk=stale.pk).exists())
        self.assertEqual(Enquiry.objects.filter(is_sample=False).count(), 0)
        self.assertEqual(Enquiry.objects.count(), 10)
        self.assertFalse(Campaign.objects.filter(is_active=False).exists())
        self.assertFalse(Campaign.objects.exclude(ends_on=None).exists())
