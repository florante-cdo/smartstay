from django.shortcuts import render

from campaigns.models import Campaign

from .models import RoomType


def landing(request):
    code = request.GET.get("utm_campaign", "")
    campaign = Campaign.objects.filter(code=code, is_active=True).first() if code else None
    rooms = RoomType.objects.filter(is_active=True)
    return render(request, "core/landing.html", {"campaign": campaign, "rooms": rooms})