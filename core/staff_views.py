from django.shortcuts import render
from django.views.decorators.cache import never_cache

from enquiries.models import Enquiry

from .permissions import role_required, user_role


@never_cache
@role_required("reception", "manager")
def staff_home(request):
    context = {
        "role": user_role(request.user),
        "total_enquiries": Enquiry.objects.count(),
        "new_enquiries": Enquiry.objects.filter(status=Enquiry.Status.NEW).count(),
    }
    return render(request, "staff/home.html", context)
