from urllib.parse import urlencode

from django.conf import settings
from django.db import models


class Campaign(models.Model):
    class Source(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        FACEBOOK = "facebook", "Facebook"
        TIKTOK = "tiktok", "TikTok"
        WHATSAPP = "whatsapp", "WhatsApp"
        QR = "qr", "QR poster"
        EMAIL = "email", "Email"
        WEBSITE = "website", "Website"

    class Medium(models.TextChoices):
        ORGANIC_SOCIAL = "organic_social", "Organic social"
        PAID_SOCIAL = "paid_social", "Paid social"
        MESSAGING = "messaging", "Messaging"
        PRINT = "print", "Print"
        EMAIL = "email", "Email"

    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=60, unique=True)
    source = models.CharField(max_length=30, choices=Source.choices)
    medium = models.CharField(max_length=30, choices=Medium.choices)
    landing_path = models.CharField(max_length=120, default="/promo/")
    headline = models.CharField(max_length=160, blank=True)
    offer_text = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    ends_on = models.DateField(null=True, blank=True, help_text="Last day the campaign runs. Leave blank to run until paused.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_sample = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.source})"

    @property
    def has_ended(self):
        from django.utils import timezone

        return self.ends_on is not None and self.ends_on < timezone.localdate()

    @property
    def status_label(self):
        if self.has_ended:
            return "Ended"
        return "Active" if self.is_active else "Paused"

    @classmethod
    def expire_overdue(cls):
        """Switch off any active campaign whose last day has passed."""
        from django.utils import timezone

        return cls.objects.filter(is_active=True, ends_on__lt=timezone.localdate()).update(is_active=False)

    def tracked_path(self):
        query = urlencode(
            {
                "utm_source": self.source,
                "utm_medium": self.medium,
                "utm_campaign": self.code,
            }
        )
        return f"{self.landing_path}?{query}"