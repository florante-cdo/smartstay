from io import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from campaigns.models import Campaign
from enquiries.models import Enquiry
from reservations.models import Reservation


class Command(BaseCommand):
    help = "Wipe everything created during a demo and restore the clean sample data."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Confirm the wipe.")
        parser.add_argument("--count", type=int, default=60, help="Sample enquiries to create.")

    def handle(self, *args, **options):
        if not settings.DEMO_MODE:
            raise CommandError("Refusing to run: DEMO_MODE is off, so this may be real data.")
        if not options["yes"]:
            raise CommandError(
                "This deletes ALL enquiries, reservations and non-sample campaigns. "
                "Run again with --yes to confirm."
            )

        with transaction.atomic():
            # Reservations first: they protect the enquiry they belong to.
            Reservation.objects.all().delete()
            Enquiry.objects.all().delete()
            Campaign.objects.filter(is_sample=False).delete()
            Campaign.objects.filter(is_sample=True).update(is_active=True, ends_on=None)

        call_command("seed_demo", count=options["count"], stdout=StringIO())

        for username in ("reception", "manager"):
            user = User.objects.filter(username=username).first()
            if user:
                user.set_password("demo12345")
                user.save(update_fields=["password"])

        self.stdout.write(self.style.SUCCESS(
            f"Demo reset: {Enquiry.objects.count()} enquiries, "
            f"{Campaign.objects.filter(is_active=True).count()} active campaigns. "
            "Logins: reception / manager, password demo12345."
        ))
