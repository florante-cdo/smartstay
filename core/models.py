from django.db import models


class RoomType(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    image = models.CharField(
        max_length=200, blank=True, help_text="Static file path, e.g. img/deluxe.jpg"
    )
    capacity = models.PositiveSmallIntegerField(default=2)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_sample = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_order", "name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1), name="roomtype_capacity_gte_1"
            )
        ]

    def __str__(self):
        return self.name

from django.conf import settings  # noqa: E402


class StaffProfile(models.Model):
    """Extra staff details that Django's built-in user does not hold."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile"
    )
    phone = models.CharField(max_length=20, blank=True)
    job_title = models.CharField(max_length=80, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def for_user(cls, user):
        profile, _ = cls.objects.get_or_create(user=user)
        return profile

    def __str__(self):
        return f"Profile for {self.user}"
