from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Enquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        PENDING_GUEST = "pending_guest", "Pending Guest"
        RESERVATION_PENDING = "reservation_pending", "Reservation Pending"
        CONFIRMED = "confirmed", "Confirmed"
        NOT_CONVERTED = "not_converted", "Not Converted"
        CANCELLED = "cancelled", "Cancelled"

    class PreferredContact(models.TextChoices):
        PHONE = "phone", "Phone call"
        WHATSAPP = "whatsapp", "WhatsApp"

    class EntryChannel(models.TextChoices):
        WEB_FORM = "web_form", "Web form"
        PHONE = "phone", "Phone call"
        WALK_IN = "walk_in", "Walk-in"
        WHATSAPP = "whatsapp", "WhatsApp"

    reference = models.CharField(
        max_length=20, unique=True, null=True, blank=True, editable=False
    )
    guest_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    preferred_contact = models.CharField(
        max_length=10, choices=PreferredContact.choices, default=PreferredContact.PHONE
    )
    requested_check_in = models.DateField()
    requested_check_out = models.DateField()
    guest_count = models.PositiveSmallIntegerField(default=1)
    room_type = models.ForeignKey(
        "core.RoomType", null=True, blank=True, on_delete=models.SET_NULL
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW
    )

    campaign = models.ForeignKey(
        "campaigns.Campaign", null=True, blank=True, on_delete=models.SET_NULL
    )
    source = models.CharField(max_length=30, default="direct")
    medium = models.CharField(max_length=30, default="direct")
    campaign_raw = models.CharField(max_length=120, blank=True)
    landing_page = models.CharField(max_length=200, blank=True)
    entry_channel = models.CharField(
        max_length=15, choices=EntryChannel.choices, default=EntryChannel.WEB_FORM
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_enquiries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_sample = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "enquiries"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["source", "campaign"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(requested_check_out__gt=F("requested_check_in")),
                name="enquiry_checkout_after_checkin",
            ),
            models.CheckConstraint(
                condition=Q(guest_count__gte=1), name="enquiry_guest_count_gte_1"
            ),
        ]

    def __str__(self):
        return f"{self.reference or 'new'} - {self.guest_name}"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.reference:
            self.reference = f"SG-{self.pk:04d}"
            super().save(update_fields=["reference"])


class EnquiryNote(models.Model):
    enquiry = models.ForeignKey(
        Enquiry, on_delete=models.CASCADE, related_name="notes"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    note = models.TextField()
    next_follow_up_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.enquiry.reference}"


class StatusChange(models.Model):
    enquiry = models.ForeignKey(
        Enquiry, on_delete=models.CASCADE, related_name="status_changes"
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.enquiry.reference}: {self.from_status} -> {self.to_status}"