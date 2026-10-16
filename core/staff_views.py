from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from dashboard.api import PERIODS
from enquiries.models import Enquiry, StatusChange

from .permissions import role_required, user_role


@never_cache
@role_required("reception", "manager")
def staff_home(request):
    now = timezone.now()
    labels = dict(Enquiry.Status.choices)

    total = Enquiry.objects.count()
    new = Enquiry.objects.filter(status=Enquiry.Status.NEW)
    needs_follow_up = new.filter(created_at__lt=now - timedelta(hours=24)).count()

    tiles = [
        {"label": "New enquiries", "hint": "Waiting for a first reply",
         "value": new.count(), "url": "?status=new", "warn": False},
        {"label": "Needs follow-up", "hint": "New for more than 24 hours",
         "value": needs_follow_up, "url": "?status=new", "warn": needs_follow_up > 0},
        {"label": "Waiting on guest", "hint": "We replied, guest has not",
         "value": Enquiry.objects.filter(status=Enquiry.Status.PENDING_GUEST).count(),
         "url": "?status=pending_guest", "warn": False},
        {"label": "Assigned to me", "hint": "Open enquiries you own",
         "value": Enquiry.objects.filter(assigned_to=request.user)
         .exclude(status__in=["confirmed", "not_converted", "cancelled"]).count(),
         "url": "?assigned=me", "warn": False},
    ]

    attention = list(new.select_related("campaign").order_by("created_at")[:5])
    for e in attention:
        e.is_overdue = e.created_at < now - timedelta(hours=24)

    activity = list(
        StatusChange.objects.select_related("enquiry", "changed_by").order_by("-changed_at")[:6]
    )
    for c in activity:
        c.to_label = labels.get(c.to_status, c.to_status)
        c.who = c.changed_by.get_full_name() or c.changed_by.username if c.changed_by else "System"

    context = {
        "role": user_role(request.user),
        "nav": "home",
        "total_enquiries": total,
        "is_manager": user_role(request.user) == "manager",
        "key": request.GET.get("days") if request.GET.get("days") in PERIODS else "30",
        "periods": [(k, v[0]) for k, v in PERIODS.items()],
        "tiles": tiles,
        "attention": attention,
        "activity": activity,
    }
    return render(request, "staff/home.html", context)
