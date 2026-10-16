from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from core.permissions import role_required, user_role
from enquiries.models import Enquiry

from . import services
from .forms import ReasonForm, ReservationForm
from .models import Reservation

PAGE_SIZE = 10

DOTS = {
    "pending": "bg-amber-500",
    "confirmed": "bg-emerald-600",
    "declined": "bg-stone-400",
    "cancelled": "bg-red-500",
}


@never_cache
@role_required("reception", "manager")
def reservation_list(request):
    choices = Reservation._meta.get_field("status").choices
    valid = [value for value, _ in choices]
    status = request.GET.get("status", "pending")

    qs = Reservation.objects.select_related("enquiry", "room_type", "created_by")
    if status in valid:
        qs = qs.filter(status=status)
    else:
        status = ""
    qs = qs.order_by("created_at" if status == "pending" else "-created_at")

    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))
    pages = list(paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1))

    rows = list(page.object_list)
    for row in rows:
        row.dot = DOTS.get(row.status, "bg-stone-400")

    counts = dict(Reservation.objects.values_list("status").annotate(n=Count("id")))
    labels = dict(choices)
    tabs = [("pending", labels.get("pending", "Pending"), counts.get("pending", 0))]
    tabs += [(v, l, counts.get(v, 0)) for v, l in choices if v != "pending"]
    tabs.append(("", "All", sum(counts.values())))

    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "reservations/list.html", {
        "role": user_role(request.user),
        "nav": "reservations",
        "rows": rows,
        "page": page,
        "pages": pages,
        "ellipsis": Paginator.ELLIPSIS,
        "status": status,
        "tabs": tabs,
        "base_query": params.urlencode(),
    })


@never_cache
@role_required("reception", "manager")
def reservation_detail(request, pk):
    res = get_object_or_404(
        Reservation.objects.select_related("enquiry", "room_type", "created_by", "confirmed_by"), pk=pk
    )
    role = user_role(request.user)
    decline_form = ReasonForm(prefix="decline")
    cancel_form = ReasonForm(prefix="cancel")

    if request.method == "POST":
        if role != "manager":
            raise PermissionDenied
        action = request.POST.get("action")
        try:
            if action == "confirm":
                services.confirm(res, request.user)
                messages.success(request, f"{res.reference} confirmed.")
                return redirect("staff_reservation", pk=res.pk)
            if action == "decline":
                decline_form = ReasonForm(request.POST, prefix="decline")
                if decline_form.is_valid():
                    services.decline(res, request.user, decline_form.cleaned_data["reason"])
                    messages.success(request, f"{res.reference} declined. The enquiry is back with reception.")
                    return redirect("staff_reservation", pk=res.pk)
            if action == "cancel":
                cancel_form = ReasonForm(request.POST, prefix="cancel")
                if cancel_form.is_valid():
                    services.cancel(res, request.user, cancel_form.cleaned_data["reason"])
                    messages.success(request, f"{res.reference} cancelled.")
                    return redirect("staff_reservation", pk=res.pk)
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
            return redirect("staff_reservation", pk=res.pk)

    return render(request, "reservations/detail.html", {
        "role": role,
        "nav": "reservations",
        "res": res,
        "enquiry": res.enquiry,
        "nights": (res.check_out - res.check_in).days,
        "dot": DOTS.get(res.status, "bg-stone-400"),
        "is_manager": role == "manager",
        "decline_form": decline_form,
        "cancel_form": cancel_form,
    })


@never_cache
@role_required("reception", "manager")
def reservation_create(request, enquiry_pk):
    enquiry = get_object_or_404(Enquiry.objects.select_related("room_type"), pk=enquiry_pk)
    if enquiry.status not in ("contacted", "pending_guest"):
        messages.error(request, "A reservation can only be requested after the guest has been contacted.")
        return redirect("staff_enquiry", pk=enquiry.pk)

    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            try:
                res = services.create_pending(
                    enquiry, request.user, d["room_type"], d["check_in"], d["check_out"],
                    d["guest_count"], d["notes"],
                )
            except ValidationError as exc:
                form.add_error(None, exc.messages[0])
            else:
                messages.success(request, f"{res.reference} requested. A manager will confirm or decline it.")
                return redirect("staff_reservation", pk=res.pk)
    else:
        form = ReservationForm(initial={
            "room_type": enquiry.room_type,
            "check_in": enquiry.requested_check_in,
            "check_out": enquiry.requested_check_out,
            "guest_count": enquiry.guest_count,
        })

    return render(request, "reservations/create.html", {
        "role": user_role(request.user),
        "nav": "reservations",
        "enquiry": enquiry,
        "form": form,
    })


@never_cache
@role_required("reception", "manager")
def reservation_quick(request, pk):
    res = get_object_or_404(
        Reservation.objects.select_related("enquiry", "room_type", "created_by", "confirmed_by"), pk=pk
    )
    return render(request, "reservations/_quick.html", {
        "res": res,
        "enquiry": res.enquiry,
        "nights": (res.check_out - res.check_in).days,
        "dot": DOTS.get(res.status, "bg-stone-400"),
        "last_note": res.enquiry.notes.select_related("author").order_by("-created_at").first(),
    })
