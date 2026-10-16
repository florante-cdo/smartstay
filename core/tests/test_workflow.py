from django.core.exceptions import ValidationError

from enquiries.models import Enquiry
from enquiries.services import change_status
from enquiries.workflow import REASON_REQUIRED, allowed_next

from .base import BaseCase

S = Enquiry.Status


def values(status):
    """allowed_next returns (value, label) pairs; compare on the value."""
    return {value for value, _label in allowed_next(status)}


class WorkflowRules(BaseCase):
    def test_new_can_only_move_to_expected_states(self):
        self.assertEqual(values(S.NEW), {S.CONTACTED, S.NOT_CONVERTED, S.CANCELLED})

    def test_final_states_have_no_moves(self):
        for state in (S.RESERVATION_PENDING, S.CONFIRMED, S.CANCELLED):
            self.assertEqual(values(state), set(), state)

    def test_nothing_can_be_confirmed_by_status_change(self):
        for state in S.values:
            self.assertNotIn(S.CONFIRMED, values(state), state)
            self.assertNotIn(S.RESERVATION_PENDING, values(state), state)

    def test_closing_states_need_a_reason(self):
        self.assertEqual(set(REASON_REQUIRED), {S.NOT_CONVERTED, S.CANCELLED})


class ChangeStatusService(BaseCase):
    def test_valid_move_is_saved_with_history(self):
        e = self.make_enquiry(status=S.NEW)
        change_status(e, S.CONTACTED, self.reception)
        e.refresh_from_db()
        self.assertEqual(e.status, S.CONTACTED)
        self.assertEqual(e.assigned_to, self.reception)
        self.assertEqual(e.status_changes.count(), 1)

    def test_invalid_move_is_refused_and_changes_nothing(self):
        e = self.make_enquiry(status=S.NEW)
        with self.assertRaises(ValidationError):
            change_status(e, S.CONFIRMED, self.reception)
        e.refresh_from_db()
        self.assertEqual(e.status, S.NEW)
        self.assertEqual(e.status_changes.count(), 0)

    def test_closing_without_a_reason_is_refused(self):
        e = self.make_enquiry(status=S.NEW)
        with self.assertRaises(ValidationError):
            change_status(e, S.NOT_CONVERTED, self.reception, "")
        change_status(e, S.NOT_CONVERTED, self.reception, "Price too high")
        e.refresh_from_db()
        self.assertEqual(e.status, S.NOT_CONVERTED)
