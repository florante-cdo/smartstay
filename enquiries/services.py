from django.db import transaction

from campaigns.models import Campaign

from .models import Enquiry, StatusChange


def attribute(utm_campaign="", utm_source="", utm_medium=""):
    """Decide the campaign, source and medium to store for a web enquiry."""
    code = (utm_campaign or "").strip().lower()
    if code:
        campaign = Campaign.objects.filter(code=code, is_active=True).first()
        if campaign:
            return {
                "campaign": campaign,
                "source": campaign.source,
                "medium": campaign.medium,
                "campaign_raw": code,
            }
        return {"campaign": None, "source": "unknown", "medium": "unknown", "campaign_raw": code[:120]}
    if utm_source or utm_medium:
        return {"campaign": None, "source": "unknown", "medium": "unknown", "campaign_raw": ""}
    return {"campaign": None, "source": "direct", "medium": "direct", "campaign_raw": ""}


@transaction.atomic
def create_web_enquiry(form, tracking, landing_page):
    """Save a guest's web enquiry with its attribution and first status record."""
    enquiry = form.save(commit=False)
    for field, value in attribute(**tracking).items():
        setattr(enquiry, field, value)
    enquiry.landing_page = landing_page[:200]
    enquiry.entry_channel = Enquiry.EntryChannel.WEB_FORM
    enquiry.status = Enquiry.Status.NEW
    enquiry.save()
    StatusChange.objects.create(
        enquiry=enquiry, from_status="", to_status=Enquiry.Status.NEW
    )
    return enquiry


def change_status(enquiry, to_status, user, reason=""):
    """Move an enquiry to a new status and record who did it and why."""
    from django.core.exceptions import ValidationError
    from django.db import transaction

    from .models import StatusChange
    from .workflow import REASON_REQUIRED, allowed_next

    if to_status not in [value for value, _ in allowed_next(enquiry.status)]:
        raise ValidationError("That status change is not allowed from here.")
    if to_status in REASON_REQUIRED and not reason.strip():
        raise ValidationError("Please give a reason.")

    with transaction.atomic():
        old = enquiry.status
        enquiry.status = to_status
        fields = ["status", "updated_at"]
        if old == "new" and enquiry.assigned_to_id is None:
            enquiry.assigned_to = user
            fields.append("assigned_to")
        enquiry.save(update_fields=fields)
        StatusChange.objects.create(
            enquiry=enquiry,
            from_status=old,
            to_status=to_status,
            changed_by=user,
            reason=reason.strip(),
        )
    return enquiry
