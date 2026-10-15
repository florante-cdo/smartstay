from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"

    reference = models.CharField(
        max_length=20, unique=True, null=True, blank=True, editable=False
    )
    enquiry = models.ForeignKey(
        "enquiries.Enquiry", on_delete=models.PROTECT, related_name="reservations"
    )
    room_type = models.ForeignKey(
        "core.RoomType", null=True, blank=True, on_delete=models.SET_NULL
    )
    check_in = models.DateField()
    check_out = models.DateField()
    guest_count = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.PENDING
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reservations_created",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reservations_confirmed",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_sample = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(check_out__gt=F("check_in")),
                name="reservation_checkout_after_checkin",
            ),
            models.CheckConstraint(
                condition=Q(guest_count__gte=1), name="reservation_guest_count_gte_1"
            ),
        ]

    def __str__(self):
        return f"{self.reference or 'new'} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.reference:
            self.reference = f"RS-{self.pk:04d}"
            super().save(update_fields=["reference"])