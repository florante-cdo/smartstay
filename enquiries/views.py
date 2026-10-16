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


from django.contrib import messages  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402
from django.shortcuts import get_object_or_404, redirect  # noqa: E402

from .forms import NoteForm, StatusForm  # noqa: E402
from .services import change_status  # noqa: E402
from .workflow import allowed_next  # noqa: E402


@never_cache
@role_required("reception", "manager")
def enquiry_detail(request, pk):
    enquiry = get_object_or_404(
        Enquiry.objects.select_related("campaign", "room_type", "assigned_to"), pk=pk
    )
    note_form = NoteForm(prefix="note")
    status_form = StatusForm(current_status=enquiry.status, prefix="st")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "note":
            note_form = NoteForm(request.POST, prefix="note")
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.enquiry = enquiry
                note.author = request.user
                note.save()
                messages.success(request, "Note added.")
                return redirect("staff_enquiry", pk=enquiry.pk)
        elif action == "status":
            status_form = StatusForm(request.POST, current_status=enquiry.status, prefix="st")
            if status_form.is_valid():
                try:
                    change_status(
                        enquiry,
                        status_form.cleaned_data["to_status"],
                        request.user,
                        status_form.cleaned_data["reason"],
                    )
                except ValidationError as exc:
                    status_form.add_error(None, exc.messages[0])
                else:
                    messages.success(request, "Status updated.")
                    return redirect("staff_enquiry", pk=enquiry.pk)
        elif action == "assign":
            enquiry.assigned_to = request.user
            enquiry.save(update_fields=["assigned_to", "updated_at"])
            messages.success(request, "This enquiry is now assigned to you.")
            return redirect("staff_enquiry", pk=enquiry.pk)

    labels = dict(Enquiry.Status.choices)
    history = list(enquiry.status_changes.select_related("changed_by").order_by("-changed_at"))
    for change in history:
        change.from_label = labels.get(change.from_status, "")
        change.to_label = labels.get(change.to_status, change.to_status)
        change.who = (
            (change.changed_by.get_full_name() or change.changed_by.username)
            if change.changed_by
            else "System"
        )

    context = {
        "role": user_role(request.user),
        "nav": "inbox",
        "enquiry": enquiry,
        "nights": (enquiry.requested_check_out - enquiry.requested_check_in).days,
        "dot": STATUS_DOTS.get(enquiry.status, "bg-stone-400"),
        "source_label": enquiry.source.replace("_", " ").title(),
        "notes": enquiry.notes.select_related("author").order_by("-created_at"),
        "history": history,
        "note_form": note_form,
        "status_form": status_form,
        "can_change": bool(allowed_next(enquiry.status)),
        "reservations": enquiry.reservations.select_related("room_type").order_by("-created_at"),
        "can_reserve": enquiry.status in ("contacted", "pending_guest"),
    }
    return render(request, "enquiries/detail.html", context)


@never_cache
@role_required("reception", "manager")
def enquiry_quick(request, pk):
    enquiry = get_object_or_404(
        Enquiry.objects.select_related("campaign", "room_type", "assigned_to"), pk=pk
    )
    return render(request, "enquiries/_quick.html", {
        "enquiry": enquiry,
        "dot": STATUS_DOTS.get(enquiry.status, "bg-stone-400"),
        "source_label": enquiry.source.replace("_", " ").title(),
        "nights": (enquiry.requested_check_out - enquiry.requested_check_in).days,
        "last_note": enquiry.notes.select_related("author").order_by("-created_at").first(),
        "reservation": enquiry.reservations.select_related("room_type").order_by("-created_at").first(),
    })
