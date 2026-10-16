from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.utils import timezone

from campaigns.models import Campaign
from core.models import RoomType
from enquiries.models import Enquiry

# Tests must not depend on collectstatic having been run.
PLAIN_STATIC = override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)


@PLAIN_STATIC
class BaseCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reception = cls._user("rita", "Reception")
        cls.manager = cls._user("mark", "Manager")
        cls.room = RoomType.objects.create(name="Standard Room", capacity=2)
        cls.campaign = Campaign.objects.create(
            name="Weekend Offer", code="weekend_offer", source="instagram", medium="social",
        )

    @staticmethod
    def _user(name, group):
        user = User.objects.create_user(name, password="x")
        user.groups.add(Group.objects.get_or_create(name=group)[0])
        return user

    def make_enquiry(self, **extra):
        today = timezone.localdate()
        fields = dict(
            guest_name="Test Guest", phone="0712345678", preferred_contact="phone",
            requested_check_in=today + timedelta(days=10),
            requested_check_out=today + timedelta(days=12),
            guest_count=2, source="direct", medium="none",
        )
        fields.update(extra)
        return Enquiry.objects.create(**fields)
