from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from core.permissions import user_role
from enquiries.models import Enquiry
from reservations.models import Reservation

PERIODS = {
    "7": ("Last 7 days", 7),
    "30": ("Last 30 days", 30),
    "90": ("Last 90 days", 90),
    "all": ("All time", None),
}

SOURCE_LABELS = {
    "direct": "Direct (no campaign)",
    "unknown": "Unknown link",
    "phone": "Phone",
    "walk_in": "Walk-in",
}


class IsManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user_role(user) == "manager")


def _nice(value):
    return (value or "").replace("_", " ").title()


def _rate(confirmed, total):
    return round(confirmed / total, 4) if total else None


def _confirmed_for(enquiries):
    return (
        Reservation.objects.filter(status="confirmed", enquiry__in=enquiries)
        .values("enquiry")
        .distinct()
        .count()
    )


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsManager])
def dashboard_summary(request):
    """Campaign -> Enquiry -> Reservation results for enquiries received in a period."""
    key = request.query_params.get("days", "30")
    if key not in PERIODS:
        key = "30"
    label, days = PERIODS[key]
    today = timezone.localdate()
    everything = Enquiry.objects.all()

    if days:
        start = today - timedelta(days=days - 1)
        cohort = everything.filter(created_at__date__gte=start)
        before = everything.filter(
            created_at__date__gte=start - timedelta(days=days), created_at__date__lt=start
        )
    else:
        start, cohort, before = None, everything, None

    total = cohort.count()
    confirmed = _confirmed_for(cohort)
    waiting = cohort.filter(status=Enquiry.Status.NEW).count()
    previous = None
    if before is not None:
        previous = {
            "enquiries": before.count(),
            "confirmed": _confirmed_for(before),
            "label": f"previous {days} days",
        }

    # Funnel: each step is a subset of the one before it.
    handled = min(cohort.exclude(status=Enquiry.Status.NEW).count(), total)
    requested = min(
        Reservation.objects.filter(enquiry__in=cohort).values("enquiry").distinct().count(), handled
    )
    funnel = [
        {"stage": "Received", "count": total},
        {"stage": "Handled by staff", "count": handled},
        {"stage": "Reservation requested", "count": requested},
        {"stage": "Confirmed", "count": min(confirmed, requested)},
    ]

    # By campaign, plus the enquiries that arrived without one.
    with_campaign = (
        cohort.filter(campaign__isnull=False)
        .order_by()
        .values("campaign", "campaign__name", "campaign__source")
        .annotate(n=Count("id"))
    )
    campaign_confirmed = dict(
        Reservation.objects.filter(status="confirmed", enquiry__in=cohort, enquiry__campaign__isnull=False)
        .order_by()
        .values_list("enquiry__campaign")
        .annotate(n=Count("enquiry", distinct=True))
    )
    without_campaign = (
        cohort.filter(campaign__isnull=True).order_by().values("source").annotate(n=Count("id"))
    )
    source_confirmed = dict(
        Reservation.objects.filter(status="confirmed", enquiry__in=cohort, enquiry__campaign__isnull=True)
        .order_by()
        .values_list("enquiry__source")
        .annotate(n=Count("enquiry", distinct=True))
    )

    rows = []
    for r in with_campaign:
        c = campaign_confirmed.get(r["campaign"], 0)
        rows.append({
            "label": r["campaign__name"],
            "detail": _nice(r["campaign__source"]),
            "kind": "campaign",
            "enquiries": r["n"],
            "confirmed": c,
            "rate": _rate(c, r["n"]),
        })
    for r in without_campaign:
        c = source_confirmed.get(r["source"], 0)
        rows.append({
            "label": SOURCE_LABELS.get(r["source"], _nice(r["source"]) + " (no campaign)"),
            "detail": "No campaign link",
            "kind": "other",
            "enquiries": r["n"],
            "confirmed": c,
            "rate": _rate(c, r["n"]),
        })
    rows.sort(key=lambda r: (-r["enquiries"], r["label"]))

    # Enquiries per day, with empty days filled in.
    daily = dict(
        cohort.annotate(d=TruncDate("created_at")).order_by("d").values_list("d").annotate(n=Count("id"))
    )
    first = start or (min(daily) if daily else today)
    trend, day = [], first
    while day <= today:
        trend.append({"date": day.isoformat(), "count": daily.get(day, 0)})
        day += timedelta(days=1)

    response = Response({
        "period": {"key": key, "label": label, "days": days, "from": first.isoformat(), "to": today.isoformat()},
        "kpis": {"enquiries": total, "confirmed": confirmed, "conversion": _rate(confirmed, total), "waiting": waiting},
        "previous": previous,
        "by_campaign": rows,
        "funnel": funnel,
        "trend": trend,
    })
    # Short private cache: repeat visits are quick, new enquiries show within seconds.
    response["Cache-Control"] = "private, max-age=15"
    response["Vary"] = "Cookie"
    return response
