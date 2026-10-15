from django.contrib import admin

from .models import Enquiry, EnquiryNote, StatusChange


class EnquiryNoteInline(admin.TabularInline):
    model = EnquiryNote
    extra = 0
    readonly_fields = ("created_at",)


class StatusChangeInline(admin.TabularInline):
    model = StatusChange
    extra = 0
    readonly_fields = ("changed_at",)


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "guest_name", "status", "source", "campaign", "created_at", "is_sample",
    )
    list_filter = ("status", "source", "entry_channel", "is_sample")
    search_fields = ("reference", "guest_name", "phone")
    readonly_fields = ("reference", "created_at", "updated_at")
    inlines = [EnquiryNoteInline, StatusChangeInline]