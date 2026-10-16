from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify

from .models import Campaign

_FIELD = (
    "mt-1 w-full rounded-md border border-garden-900/20 bg-white px-3 py-2 text-sm "
    "focus:border-garden-600 focus:outline-none focus:ring-2 focus:ring-garden-600/30"
)
_CHECK = "h-4 w-4 rounded border-garden-900/30 text-garden-700 focus:ring-garden-600"


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["name", "code", "source", "medium", "landing_path", "headline", "offer_text", "ends_on", "is_active"]
        labels = {
            "name": "Campaign name",
            "code": "Campaign code",
            "source": "Where it runs",
            "medium": "How it runs",
            "landing_path": "Landing page path",
            "headline": "Page headline (optional)",
            "offer_text": "Offer text (optional)",
            "ends_on": "Last day (optional)",
            "is_active": "Active",
        }
        help_texts = {
            "code": "Used in the link. Leave blank to make one from the name.",
            "landing_path": "Which page guests land on, for example /promo/.",
            "headline": "Shown at the top of the landing page for this campaign.",
            "offer_text": "A line or two describing the offer.",
            "ends_on": "The campaign switches itself off after this day. Leave blank to run until paused.",
            "is_active": "When off, anyone opening this campaign's link sees an 'offer ended' page instead.",
        }
        widgets = {
            "offer_text": forms.Textarea(attrs={"rows": 3}),
            "ends_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = _CHECK if isinstance(field.widget, forms.CheckboxInput) else _FIELD
        if self.instance.pk:
            self.fields["code"].disabled = True
            self.fields["code"].help_text = "Links already shared use this code, so it can't be changed."
        else:
            self.fields["code"].required = False

    def clean(self):
        data = super().clean()
        ends_on, active = data.get("ends_on"), data.get("is_active")
        if ends_on and active and ends_on < timezone.localdate():
            self.add_error(
                "ends_on",
                "This date has passed. Choose a later date to run the campaign again, or untick Active.",
            )
        return data

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().lower()
        if not code:
            code = slugify(self.data.get("name", "")).replace("-", "_")
        if not code:
            raise ValidationError("Enter a campaign name or a code.")
        return code

    def clean_landing_path(self):
        path = self.cleaned_data["landing_path"].strip()
        if not path.startswith("/") or path.startswith("//") or " " in path:
            raise ValidationError("Use a page on this site, such as /promo/.")
        return path
