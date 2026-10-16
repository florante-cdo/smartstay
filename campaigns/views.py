from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from core.permissions import role_required, user_role
from enquiries.models import Enquiry
from reservations.models import Reservation

from .forms import CampaignForm
from .models import Campaign

PAGE_SIZE = 10


def _full_url(campaign):
    return settings.SITE_URL + campaign.tracked_path()


def _counts(ids):
    """Enquiries and confirmed reservations per campaign: Campaign -> Enquiry -> Reservation."""
    enquiries = dict(
        Enquiry.objects.filter(campaign_id__in=ids).order_by()
        .values_list("campaign").annotate(n=Count("id"))
    )
    confirmed = dict(
        Reservation.objects.filter(status="confirmed", enquiry__campaign_id__in=ids).order_by()
        .values_list("enquiry__campaign").annotate(n=Count("id"))
    )
    return enquiries, confirmed


@never_cache
@role_required("manager")
def campaign_list(request):
    Campaign.expire_overdue()
    paginator = Paginator(Campaign.objects.order_by("-is_active", "name"), PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))
    pages = list(paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1))

    rows = list(page.object_list)
    enquiries, confirmed = _counts([c.pk for c in rows])
    for c in rows:
        c.enquiry_total = enquiries.get(c.pk, 0)
        c.confirmed_total = confirmed.get(c.pk, 0)

    return render(request, "campaigns/list.html", {
        "role": user_role(request.user),
        "nav": "campaigns",
        "rows": rows,
        "page": page,
        "pages": pages,
        "ellipsis": Paginator.ELLIPSIS,
        "base_query": "",
    })


@never_cache
@role_required("manager")
def campaign_quick(request, pk):
    campaign = get_object_or_404(Campaign.objects.select_related("created_by"), pk=pk)
    enquiries, confirmed = _counts([campaign.pk])
    return render(request, "campaigns/_quick.html", {
        "c": campaign,
        "full_url": _full_url(campaign),
        "enquiry_total": enquiries.get(campaign.pk, 0),
        "confirmed_total": confirmed.get(campaign.pk, 0),
    })


@never_cache
@role_required("manager")
def campaign_create(request):
    form = CampaignForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        campaign = form.save(commit=False)
        campaign.created_by = request.user
        campaign.save()
        messages.success(request, f"{campaign.name} created. Its link and QR code are under View.")
        return redirect("staff_campaigns")
    return render(request, "campaigns/form.html", {
        "role": user_role(request.user), "nav": "campaigns", "form": form, "creating": True,
    })


@never_cache
@role_required("manager")
def campaign_edit(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    form = CampaignForm(request.POST or None, instance=campaign)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{campaign.name} updated.")
        return redirect("staff_campaigns")
    return render(request, "campaigns/form.html", {
        "role": user_role(request.user), "nav": "campaigns", "form": form,
        "creating": False, "campaign": campaign,
    })


@never_cache
@role_required("manager")
def campaign_qr(request, pk):
    """A self-contained SVG QR code for the campaign's tracked link."""
    import qrcode

    campaign = get_object_or_404(Campaign, pk=pk)
    qr = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(_full_url(campaign))
    qr.make(fit=True)
    matrix = qr.get_matrix()
    size = len(matrix)
    path = "".join(
        f"M{x},{y}h1v1h-1z" for y, row in enumerate(matrix) for x, filled in enumerate(row) if filled
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" shape-rendering="crispEdges">'
        f'<rect width="{size}" height="{size}" fill="#ffffff"/><path d="{path}" fill="#142e22"/></svg>'
    )
    response = HttpResponse(svg, content_type="image/svg+xml")
    if request.GET.get("download"):
        response["Content-Disposition"] = f'attachment; filename="{campaign.code}-qr.svg"'
    return response
