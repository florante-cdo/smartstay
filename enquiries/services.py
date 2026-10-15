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
