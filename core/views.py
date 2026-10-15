from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from campaigns.models import Campaign
from enquiries.forms import EnquiryForm
from enquiries.services import create_web_enquiry

from .models import RoomType

TRACKING_KEYS = ("utm_source", "utm_medium", "utm_campaign")
RATE_WINDOW_SECONDS = 60 * 60


def _rate_key(request):
    return f"enquiry-rate:{request.META.get('REMOTE_ADDR', 'unknown')}"


@never_cache
def landing(request):
    code = request.GET.get("utm_campaign", "").strip().lower()
    campaign = Campaign.objects.filter(code=code, is_active=True).first() if code else None

    if request.method == "POST":
        form = EnquiryForm(request.POST)
        if form.is_valid():
            key = _rate_key(request)
            limit = 50 if settings.DEMO_MODE else 5
            sent = cache.get(key, 0)
            if sent >= limit:
                form.add_error(None, "Too many enquiries from this connection. Please try again later.")
            else:
                tracking = {
                    k: form.cleaned_data.get(k) or request.GET.get(k, "")
                    for k in TRACKING_KEYS
                }
                enquiry = create_web_enquiry(form, tracking, landing_page=request.path)
                cache.set(key, sent + 1, RATE_WINDOW_SECONDS)
                request.session["last_enquiry_reference"] = enquiry.reference
                return redirect("enquiry_thanks")
    else:
        form = EnquiryForm()

    rooms = RoomType.objects.filter(is_active=True)
    return render(request, "core/landing.html", {"campaign": campaign, "rooms": rooms, "form": form})


@never_cache
def enquiry_thanks(request):
    reference = request.session.get("last_enquiry_reference")
    if not reference:
        return redirect("home")
    return render(request, "core/thanks.html", {"reference": reference})
