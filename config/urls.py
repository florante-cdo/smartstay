from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from core import staff_views
from core.views import landing

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", landing, name="home"),
    path("promo/", landing, name="promo"),
    path(
        "staff/login/",
        LoginView.as_view(template_name="staff/login.html", redirect_authenticated_user=True),
        name="staff_login",
    ),
    path("staff/logout/", LogoutView.as_view(), name="staff_logout"),
    path("staff/", staff_views.staff_home, name="staff_home"),
]
