from django.conf import settings


def demo(request):
    return {"demo_mode": settings.DEMO_MODE}

def staff_nav(request):
    """Counts shown in the staff sidebar. Only runs on staff pages."""
    if not request.path.startswith("/staff/") or not request.user.is_authenticated:
        return {}
    from enquiries.models import Enquiry

    return {"nav_new_count": Enquiry.objects.filter(status=Enquiry.Status.NEW).count()}
