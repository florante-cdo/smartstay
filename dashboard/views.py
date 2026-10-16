from django.shortcuts import redirect
from django.urls import reverse

from core.permissions import role_required


@role_required("manager")
def dashboard(request):
    """The dashboard now lives on the Overview page. Old links land on its Performance tab."""
    days = request.GET.get("days", "")
    suffix = f"&days={days}" if days else ""
    return redirect(f"{reverse('staff_home')}?view=performance{suffix}")
