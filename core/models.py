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