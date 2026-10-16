from functools import wraps

from django.shortcuts import render

from campaigns.models import Campaign


def campaign_ended_gate(view):
    """Show an 'offer ended' page when a link's campaign exists but is paused.

    Unknown or missing codes are not handled here: they go through to the normal
    landing page and are recorded as unknown or direct.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        Campaign.expire_overdue()
        if request.method == "GET":
            code = request.GET.get("utm_campaign", "").strip()
            if code:
                campaign = Campaign.objects.filter(code=code, is_active=False).first()
                if campaign:
                    return render(request, "core/campaign_ended.html", {"campaign": campaign})
        return view(request, *args, **kwargs)

    return wrapper
