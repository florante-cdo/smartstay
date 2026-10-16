from django.shortcuts import render
from django.views.decorators.cache import never_cache

from core.permissions import role_required, user_role

from .api import PERIODS


@never_cache
@role_required("manager")
def dashboard(request):
    key = request.GET.get("days", "30")
    if key not in PERIODS:
        key = "30"
    return render(request, "dashboard/dashboard.html", {
        "role": user_role(request.user),
        "nav": "dashboard",
        "key": key,
        "periods": [(k, v[0]) for k, v in PERIODS.items()],
    })
