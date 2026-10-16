from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from enquiries.models import Enquiry
from reservations import services
from reservations.models import Reservation

from .base import BaseCase

S = Enquiry.Status


class ReservationLifecycle(BaseCase):
    def pending(self, enquiry=None):
        enquiry = enquiry or self.make_enquiry(status=S.CONTACTED)
        today = timezone.localdate()
        return services.create_pending(
            enquiry, self.reception, self.room,
            today + timedelta(days=10), today + timedelta(days=12), 2,
        )

    def test_cannot_request_before_guest_is_contacted(self):
        with self.assertRaises(ValidationError):
            self.pending(self.make_enquiry(status=S.NEW))

    def test_requesting_moves_enquiry_to_reservation_pending(self):
        res = self.pending()
        res.enquiry.refresh_from_db()
        self.assertEqual(res.enquiry.status, S.RESERVATION_PENDING)
        self.assertEqual(res.status, "pending")

    def test_confirm_marks_both_confirmed(self):
        res = self.pending()
        services.confirm(res, self.manager)
        res.refresh_from_db()
        res.enquiry.refresh_from_db()
        self.assertEqual(res.status, "confirmed")
        self.assertEqual(res.enquiry.status, S.CONFIRMED)

    def test_confirm_twice_is_refused(self):
        res = self.pending()
        services.confirm(res, self.manager)
        with self.assertRaises(ValidationError):
            services.confirm(res, self.manager)

    def test_decline_needs_a_reason(self):
        res = self.pending()
        with self.assertRaises(ValidationError):
            services.decline(res, self.manager, "")

    def test_decline_returns_enquiry_to_contacted(self):
        res = self.pending()
        services.decline(res, self.manager, "Fully booked")
        res.refresh_from_db()
        res.enquiry.refresh_from_db()
        self.assertEqual(res.status, "declined")
        self.assertEqual(res.enquiry.status, S.CONTACTED)

    def test_only_confirmed_can_be_cancelled(self):
        res = self.pending()
        with self.assertRaises(ValidationError):
            services.cancel(res, self.manager, "Guest changed plans")
        services.confirm(res, self.manager)
        services.cancel(res, self.manager, "Guest changed plans")
        res.enquiry.refresh_from_db()
        self.assertEqual(res.enquiry.status, S.CANCELLED)

    def test_every_move_leaves_a_history_row(self):
        res = self.pending()
        services.confirm(res, self.manager)
        self.assertGreaterEqual(res.enquiry.status_changes.count(), 2)


class ReservationRoles(BaseCase):
    def test_reception_post_cannot_confirm(self):
        enquiry = self.make_enquiry(status=S.CONTACTED)
        today = timezone.localdate()
        res = services.create_pending(
            enquiry, self.reception, self.room,
            today + timedelta(days=10), today + timedelta(days=12), 2,
        )
        self.client.force_login(self.reception)
        self.client.post(f"/staff/reservations/{res.pk}/", {"action": "confirm"})
        res.refresh_from_db()
        self.assertEqual(Reservation.objects.get(pk=res.pk).status, "pending")
