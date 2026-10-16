from datetime import timedelta

from django.utils import timezone

from campaigns.models import Campaign

from .base import BaseCase


class CampaignExpiry(BaseCase):
    def test_overdue_campaign_is_switched_off(self):
        self.campaign.ends_on = timezone.localdate() - timedelta(days=1)
        self.campaign.save()
        Campaign.expire_overdue()
        self.campaign.refresh_from_db()
        self.assertFalse(self.campaign.is_active)

    def test_campaign_ending_today_stays_active(self):
        self.campaign.ends_on = timezone.localdate()
        self.campaign.save()
        Campaign.expire_overdue()
        self.campaign.refresh_from_db()
        self.assertTrue(self.campaign.is_active)

    def test_campaign_without_end_date_is_untouched(self):
        Campaign.expire_overdue()
        self.campaign.refresh_from_db()
        self.assertTrue(self.campaign.is_active)


class LandingGate(BaseCase):
    def test_paused_campaign_shows_offer_ended_page(self):
        self.campaign.is_active = False
        self.campaign.save()
        response = self.client.get("/promo/?utm_campaign=weekend_offer")
        self.assertTemplateUsed(response, "core/campaign_ended.html")

    def test_active_campaign_shows_the_landing_page(self):
        response = self.client.get("/promo/?utm_campaign=weekend_offer")
        self.assertTemplateNotUsed(response, "core/campaign_ended.html")
        self.assertEqual(response.status_code, 200)

    def test_unknown_code_still_shows_the_landing_page(self):
        response = self.client.get("/promo/?utm_campaign=nonsense")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, "core/campaign_ended.html")
