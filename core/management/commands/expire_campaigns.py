from django.core.management.base import BaseCommand

from campaigns.models import Campaign


class Command(BaseCommand):
    help = "Switch off campaigns whose last day has passed."

    def handle(self, *args, **options):
        count = Campaign.expire_overdue()
        self.stdout.write(self.style.SUCCESS(f"Expired {count} campaign(s)."))
