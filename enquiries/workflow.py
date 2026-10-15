from .models import Enquiry

S = Enquiry.Status

# Where each status may go next. Reservation Pending and Confirmed are set by
# the reservation steps, not by hand, so they have no manual way out.
TRANSITIONS = {
    S.NEW: [S.CONTACTED, S.NOT_CONVERTED, S.CANCELLED],
    S.CONTACTED: [S.PENDING_GUEST, S.NOT_CONVERTED, S.CANCELLED],
    S.PENDING_GUEST: [S.CONTACTED, S.NOT_CONVERTED, S.CANCELLED],
    S.NOT_CONVERTED: [S.CONTACTED],
    S.RESERVATION_PENDING: [],
    S.CONFIRMED: [],
    S.CANCELLED: [],
}

REASON_REQUIRED = {S.NOT_CONVERTED, S.CANCELLED}


def allowed_next(status):
    return [(s.value, s.label) for s in TRANSITIONS.get(status, [])]
