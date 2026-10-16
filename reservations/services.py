from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from enquiries.models import Enquiry, StatusChange

from .models import Reservation


def _move_enquiry(enquiry, to_status, user, reason=""):
    old = enquiry.status
    if old == to_status:
        return
    enquiry.status = to_status
    enquiry.save(update_fields=["status", "updated_at"])
    StatusChange.objects.create(
        enquiry=enquiry,
        from_status=old,
        to_status=to_status,
        changed_by=user,
        reason=reason[:200],
    )


def create_pending(enquiry, user, room_type, check_in, check_out, guest_count, notes=""):
    if enquiry.status not in (Enquiry.Status.CONTACTED, Enquiry.Status.PENDING_GUEST):
        raise ValidationError("A reservation can only be requested after the guest has been contacted.")
    with transaction.atomic():
        res = Reservation.objects.create(
            enquiry=enquiry,
            room_type=room_type,
            check_in=check_in,
            check_out=check_out,
            guest_count=guest_count,
            status="pending",
            created_by=user,
            notes=notes,
        )
        _move_enquiry(enquiry, Enquiry.Status.RESERVATION_PENDING, user, f"Reservation {res.reference} requested")
    return res


def confirm(res, user):
    if res.status != "pending":
        raise ValidationError("Only a pending reservation can be confirmed.")
    with transaction.atomic():
        res.status = "confirmed"
        res.confirmed_by = user
        res.confirmed_at = timezone.now()
        res.save(update_fields=["status", "confirmed_by", "confirmed_at"])
        _move_enquiry(res.enquiry, Enquiry.Status.CONFIRMED, user, f"Reservation {res.reference} confirmed")


def decline(res, user, reason):
    if res.status != "pending":
        raise ValidationError("Only a pending reservation can be declined.")
    if not reason.strip():
        raise ValidationError("Please give a reason.")
    with transaction.atomic():
        res.status = "declined"
        res.cancellation_reason = reason.strip()[:200]
        res.save(update_fields=["status", "cancellation_reason"])
        # The guest is still interested: send the enquiry back so reception can offer other dates.
        _move_enquiry(res.enquiry, Enquiry.Status.CONTACTED, user, f"Reservation declined: {reason.strip()}")


def cancel(res, user, reason):
    if res.status != "confirmed":
        raise ValidationError("Only a confirmed reservation can be cancelled.")
    if not reason.strip():
        raise ValidationError("Please give a reason.")
    with transaction.atomic():
        res.status = "cancelled"
        res.cancellation_reason = reason.strip()[:200]
        res.save(update_fields=["status", "cancellation_reason"])
        _move_enquiry(res.enquiry, Enquiry.Status.CANCELLED, user, f"Reservation cancelled: {reason.strip()}")
