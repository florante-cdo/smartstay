from django.conf import settings


def demo(request):
    return {"demo_mode": settings.DEMO_MODE}