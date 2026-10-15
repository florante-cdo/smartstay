from enquiries.views import enquiry_detail
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from core import staff_views
from core.views import enquiry_thanks, landing
from enquiries import views as enquiry_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", landing, name="home"),
    path("promo/", landing, name="promo"),
    path("thanks/", enquiry_thanks, name="enquiry_thanks"),
    path(
        "staff/login/",
        LoginView.as_view(template_name="staff/login.html", redirect_authenticated_user=True),
        name="staff_login",
    ),
    path("staff/logout/", LogoutView.as_view(), name="staff_logout"),
    path("staff/", staff_views.staff_home, name="staff_home"),
    path("staff/inbox/", enquiry_views.inbox, name="staff_inbox"),
    path("staff/enquiries/<int:pk>/", enquiry_detail, name="staff_enquiry"),
]
