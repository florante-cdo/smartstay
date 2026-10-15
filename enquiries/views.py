from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from core.permissions import role_required, user_role

from .models import Enquiry

PAGE_SIZE = 10

STATUS_DOTS = {
    "new": "bg-sky-500",
    "contacted": "bg-indigo-500",
    "pending_guest": "bg-amber-500",
    "reservation_pending": "bg-violet-500",
    "confirmed": "bg-emerald-600",
    "not_converted": "bg-stone-400",
    "cancelled": "bg-red-500",
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

    paginator = Paginator(enquiries, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))
    pages = list(paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1))

    overdue_before = timezone.now() - timedelta(hours=24)
    rows = list(page.object_list)
    for row in rows:
        row.dot = STATUS_DOTS.get(row.status, "bg-stone-400")
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
        "pages": pages,
        "ellipsis": Paginator.ELLIPSIS,
        "status": status,
        "source": source,
        "query": query,
        "status_tabs": status_tabs,
        "source_options": source_options,
        "base_query": params.urlencode(),
    }
    return render(request, "enquiries/inbox.html", context)
