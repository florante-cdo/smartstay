from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "enquiry", "room_type", "check_in", "check_out", "status", "is_sample",
    )
    list_filter = ("status", "is_sample")
    search_fields = ("reference", "enquiry__reference", "enquiry__guest_name")
    readonly_fields = ("reference", "created_at")