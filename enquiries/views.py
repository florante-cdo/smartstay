from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from core.permissions import role_required, user_role

from .models import Enquiry

PAGE_SIZE = 15

STATUS_STYLES = {
    "new": "bg-sky-100 text-sky-800",
    "contacted": "bg-indigo-100 text-indigo-800",
    "pending_guest": "bg-amber-100 text-amber-800",
    "reservation_pending": "bg-violet-100 text-violet-800",
    "confirmed": "bg-emerald-100 text-emerald-800",
    "not_converted": "bg-stone-200 text-stone-700",
    "cancelled": "bg-red-100 text-red-800",
}


@never_cache
@role_required("reception", "manager")
def inbox(request):
    status = request.GET.get("status", "")
    source = request.GET.get("source", "")
    query = request.GET.get("q", "").strip()

    enquiries = Enquiry.objects.select_related("campaign", "room_type", "assigned_to")
    if status in Enquiry.Status.values:
        enquiries = enquiries.filter(status=status)
    else:
        status = ""
    if source:
        enquiries = enquiries.filter(source=source)
    if query:
        enquiries = enquiries.filter(
            Q(guest_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(reference__icontains=query)
        )

    page = Paginator(enquiries, PAGE_SIZE).get_page(request.GET.get("page"))

    overdue_before = timezone.now() - timedelta(hours=24)
    rows = list(page.object_list)
    for row in rows:
        row.badge = STATUS_STYLES.get(row.status, "")
        row.source_label = row.source.replace("_", " ").title()
        row.needs_follow_up = (
            row.status == Enquiry.Status.NEW and row.created_at < overdue_before
        )

    counts = dict(Enquiry.objects.values_list("status").annotate(n=Count("id")))
    status_tabs = [("", "All", sum(counts.values()))] + [
        (value, label, counts.get(value, 0)) for value, label in Enquiry.Status.choices
    ]
    source_options = [
        (s, s.replace("_", " ").title())
        for s in Enquiry.objects.order_by("source").values_list("source", flat=True).distinct()
    ]

    params = request.GET.copy()
    params.pop("page", None)

    context = {
        "role": user_role(request.user),
        "nav": "inbox",
        "rows": rows,
        "page": page,
        "status": status,
        "source": source,
        "query": query,
        "status_tabs": status_tabs,
        "source_options": source_options,
        "base_query": params.urlencode(),
    }
    return render(request, "enquiries/inbox.html", context)
