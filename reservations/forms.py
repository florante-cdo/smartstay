from django import forms
from django.utils import timezone

from core.models import RoomType

_FIELD = (
    "mt-1 w-full rounded-md border border-garden-900/20 bg-white px-3 py-2 text-sm "
    "focus:border-garden-600 focus:outline-none focus:ring-2 focus:ring-garden-600/30"
)


class ReservationForm(forms.Form):
    room_type = forms.ModelChoiceField(
        queryset=RoomType.objects.none(),
        empty_label="Choose a room type",
        widget=forms.Select(attrs={"class": _FIELD}),
    )
    check_in = forms.DateField(
        label="Check-in",
        widget=forms.DateInput(attrs={"type": "date", "class": _FIELD}, format="%Y-%m-%d"),
    )
    check_out = forms.DateField(
        label="Check-out",
        widget=forms.DateInput(attrs={"type": "date", "class": _FIELD}, format="%Y-%m-%d"),
    )
    guest_count = forms.IntegerField(
        label="Guests", min_value=1, widget=forms.NumberInput(attrs={"class": _FIELD})
    )
    notes = forms.CharField(
        required=False,
        label="Notes for the manager",
        widget=forms.Textarea(attrs={"rows": 3, "class": _FIELD, "placeholder": "Anything the manager should know"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["room_type"]
        field.queryset = RoomType.objects.filter(is_active=True).order_by("display_order", "name")
        field.label_from_instance = lambda room: f"{room.name} (sleeps {room.capacity})"

    def clean(self):
        data = super().clean()
        check_in, check_out = data.get("check_in"), data.get("check_out")
        room, guests = data.get("room_type"), data.get("guest_count")
        if check_in and check_in < timezone.localdate():
            self.add_error("check_in", "Check-in cannot be in the past.")
        if check_in and check_out and check_out <= check_in:
            self.add_error("check_out", "Check-out must be after check-in.")
        if room and guests and guests > room.capacity:
            self.add_error("guest_count", f"{room.name} sleeps up to {room.capacity}. Choose a larger room type.")
        return data


class ReasonForm(forms.Form):
    reason = forms.CharField(
        max_length=200,
        label="Reason",
        widget=forms.TextInput(attrs={"class": _FIELD, "placeholder": "Why?"}),
    )
