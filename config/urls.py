from dashboard import views as dashboard_views
from dashboard import api as dashboard_api
from campaigns import views as campaign_views
from reservations import views as reservation_views
from core.profile_views import profile as staff_profile_view
from core import team_views
from enquiries.views import enquiry_create, enquiry_detail, enquiry_quick
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
    path("staff/enquiries/new/", enquiry_create, name="staff_enquiry_new"),
    path("staff/profile/", staff_profile_view, name="staff_profile"),
    path("staff/team/", team_views.team_list, name="staff_team"),
    path("staff/team/new/", team_views.team_new, name="staff_team_new"),
    path("staff/team/<int:pk>/", team_views.team_member, name="staff_team_member"),
    path("staff/dashboard/", dashboard_views.dashboard, name="staff_dashboard"),
    path("api/v1/dashboard/", dashboard_api.dashboard_summary, name="api_dashboard"),
    path("staff/campaigns/", campaign_views.campaign_list, name="staff_campaigns"),
    path("staff/campaigns/new/", campaign_views.campaign_create, name="staff_campaign_new"),
    path("staff/campaigns/<int:pk>/edit/", campaign_views.campaign_edit, name="staff_campaign_edit"),
    path("staff/campaigns/<int:pk>/quick/", campaign_views.campaign_quick, name="staff_campaign_quick"),
    path("staff/campaigns/<int:pk>/qr.svg", campaign_views.campaign_qr, name="staff_campaign_qr"),
    path("staff/enquiries/<int:pk>/quick/", enquiry_quick, name="staff_enquiry_quick"),
    path("staff/reservations/<int:pk>/quick/", reservation_views.reservation_quick, name="staff_reservation_quick"),
    path("staff/reservations/", reservation_views.reservation_list, name="staff_reservations"),
    path("staff/reservations/<int:pk>/", reservation_views.reservation_detail, name="staff_reservation"),
    path("staff/enquiries/<int:enquiry_pk>/reserve/", reservation_views.reservation_create, name="staff_reservation_create"),
]
