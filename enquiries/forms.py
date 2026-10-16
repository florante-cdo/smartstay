import re

from django import forms
from django.utils import timezone

from core.models import RoomType

from .models import Enquiry

INPUT_CLASS = (
    "mt-1 w-full rounded-md border border-garden-900/20 bg-white px-3 py-2 "
    "focus:border-garden-600 focus:outline-none focus:ring-2 focus:ring-garden-600/30"
)


class EnquiryForm(forms.ModelForm):
    # Filled in by the browser from the campaign link. Never trusted for source or medium.
    utm_source = forms.CharField(required=False, max_length=120, widget=forms.HiddenInput)
    utm_medium = forms.CharField(required=False, max_length=120, widget=forms.HiddenInput)
    utm_campaign = forms.CharField(required=False, max_length=120, widget=forms.HiddenInput)
    # Spam trap: hidden from people, so only bots fill it in.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

    class Meta:
        model = Enquiry
        fields = [
            "guest_name",
            "phone",
            "preferred_contact",
            "requested_check_in",
            "requested_check_out",
            "guest_count",
            "room_type",
            "message",
        ]
        labels = {
            "guest_name": "Your name",
            "phone": "Phone or WhatsApp number",
            "preferred_contact": "Best way to reach you",
            "requested_check_in": "Check-in",
            "requested_check_out": "Check-out",
            "guest_count": "Guests",
            "room_type": "Room preference",
            "message": "Anything we should know?",
        }
        widgets = {
            "requested_check_in": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "requested_check_out": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "message": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room_type"].queryset = RoomType.objects.filter(is_active=True)
        self.fields["room_type"].empty_label = "No preference"
        self.fields["guest_count"].min_value = 1
        for field in self.visible_fields():
            field.field.widget.attrs["class"] = INPUT_CLASS

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if not re.fullmatch(r"\+?[0-9 ()-]+", phone) or not 9 <= len(digits) <= 15:
            raise forms.ValidationError("Enter a valid phone number, for example 0712 345 678.")
        return phone

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Could not send this enquiry.")
        return ""

    def clean(self):
        data = super().clean()
        check_in = data.get("requested_check_in")
        check_out = data.get("requested_check_out")
        if check_in and check_in < timezone.localdate():
            self.add_error("requested_check_in", "Check-in cannot be in the past.")
        if check_in and check_out and check_out <= check_in:
            self.add_error("requested_check_out", "Check-out must be after check-in.")
        room, count = data.get("room_type"), data.get("guest_count")
        if room and count and count > room.capacity:
            self.add_error("guest_count", f"The {room.name} sleeps up to {room.capacity} guests.")
        return data


from django import forms  # noqa: E402

from .models import EnquiryNote  # noqa: E402
from .workflow import REASON_REQUIRED, allowed_next  # noqa: E402

_FIELD = (
    "mt-1 w-full rounded-md border border-garden-900/20 bg-white px-3 py-2 text-sm "
    "focus:border-garden-600 focus:outline-none focus:ring-2 focus:ring-garden-600/30"
)


class NoteForm(forms.ModelForm):
    next_follow_up_at = forms.DateTimeField(
        required=False,
        label="Follow up on",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": _FIELD}, format="%Y-%m-%dT%H:%M"
        ),
    )

    class Meta:
        model = EnquiryNote
        fields = ["note", "next_follow_up_at"]
        labels = {"note": "Add a note"}
        widgets = {
            "note": forms.Textarea(
                attrs={"rows": 3, "class": _FIELD, "placeholder": "What was said or agreed?"}
            )
        }


class StatusForm(forms.Form):
    to_status = forms.ChoiceField(label="Move to", widget=forms.Select(attrs={"class": _FIELD}))
    reason = forms.CharField(
        required=False,
        max_length=200,
        label="Reason",
        widget=forms.TextInput(attrs={"class": _FIELD, "placeholder": "Needed for Not converted and Cancelled"}),
    )

    def __init__(self, *args, current_status, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["to_status"].choices = allowed_next(current_status)

    def clean(self):
        data = super().clean()
        if data.get("to_status") in REASON_REQUIRED and not data.get("reason", "").strip():
            self.add_error("reason", "Please give a reason.")
        return data


import re  # noqa: E402

from django.utils import timezone  # noqa: E402

from campaigns.models import Campaign  # noqa: E402
from core.models import RoomType  # noqa: E402

from .models import Enquiry  # noqa: E402

CHANNELS = [("phone", "Phone call"), ("walk_in", "Walk-in"), ("whatsapp", "WhatsApp message")]


class StaffEnquiryForm(forms.ModelForm):
    channel = forms.ChoiceField(label="How did it come in?", choices=CHANNELS)
    campaign = forms.ModelChoiceField(
        label="Campaign the guest mentioned (optional)",
        queryset=Campaign.objects.none(),
        required=False,
        empty_label="None, or not sure",
        help_text="If the guest says where they saw us, pick it so the campaign gets the credit.",
    )

    class Meta:
        model = Enquiry
        fields = [
            "guest_name", "phone", "preferred_contact", "requested_check_in",
            "requested_check_out", "guest_count", "room_type", "message",
        ]
        labels = {
            "guest_name": "Guest name",
            "phone": "Phone number",
            "preferred_contact": "Best way to reach them",
            "requested_check_in": "Check-in",
            "requested_check_out": "Check-out",
            "guest_count": "Guests",
            "room_type": "Room type (optional)",
            "message": "What the guest asked for",
        }
        widgets = {
            "requested_check_in": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "requested_check_out": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "message": forms.Textarea(attrs={"rows": 3}),
        }

    field_order = [
        "channel", "guest_name", "phone", "preferred_contact", "requested_check_in",
        "requested_check_out", "guest_count", "room_type", "message", "campaign",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["campaign"].queryset = Campaign.objects.filter(is_active=True).order_by("name")
        room = self.fields["room_type"]
        room.required = False
        room.queryset = RoomType.objects.filter(is_active=True).order_by("display_order", "name")
        room.empty_label = "No preference"
        room.label_from_instance = lambda r: f"{r.name} (sleeps {r.capacity})"
        for field in self.fields.values():
            field.widget.attrs["class"] = _FIELD

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not re.fullmatch(r"[+0-9 ()\-]{7,20}", phone):
            raise forms.ValidationError("Enter a phone number, for example 0712 345 678.")
        return phone

    def clean(self):
        data = super().clean()
        check_in, check_out = data.get("requested_check_in"), data.get("requested_check_out")
        room, guests = data.get("room_type"), data.get("guest_count")
        if check_in and check_in < timezone.localdate():
            self.add_error("requested_check_in", "Check-in cannot be in the past.")
        if check_in and check_out and check_out <= check_in:
            self.add_error("requested_check_out", "Check-out must be after check-in.")
        if room and guests and guests > room.capacity:
            self.add_error("guest_count", f"{room.name} sleeps up to {room.capacity}. Choose a larger room type.")
        return data
