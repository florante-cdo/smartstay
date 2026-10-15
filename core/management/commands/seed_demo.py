import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from campaigns.models import Campaign
from core.models import RoomType
from enquiries.models import Enquiry, EnquiryNote, StatusChange
from reservations.models import Reservation

S = Enquiry.Status
DEMO_PASSWORD = "demo12345"

ROOMS = [
    ("Standard Room", 2, "A comfortable room for one or two guests. Sample description."),
    ("Deluxe Room", 2, "More space, a garden view and a work desk. Sample description."),
    ("Family Suite", 4, "Two rooms joined together for families. Sample description."),
    ("Garden Cottage", 3, "A private cottage set in the gardens. Sample description."),
]

CAMPAIGNS = [
    ("Weekend Offer", "weekend_offer", "instagram", "organic_social",
     "Weekend getaway, made simple",
     "Friday to Sunday stays with breakfast included. Sample offer text."),
    ("Honeymoon Package", "honeymoon_package", "facebook", "paid_social",
     "Begin your story at Starwood Gardens",
     "A quiet room, a garden dinner and a late checkout. Sample offer text."),
    ("WhatsApp Broadcast", "whatsapp_broadcast", "whatsapp", "messaging",
     "Special rates for returning guests",
     "A thank-you offer for past guests. Sample offer text."),
    ("Reception QR Poster", "qr_poster", "qr", "print",
     "Welcome to Starwood Gardens",
     "Scan, tell us your dates and we will reply. Sample offer text."),
    ("TikTok Garden Clips", "tiktok_clips", "tiktok", "organic_social",
     "See the gardens, then stay",
     "Short clips, simple booking. Sample offer text."),
]

FIRST_NAMES = ["Amina", "Brian", "Cynthia", "David", "Esther", "Felix", "Grace",
               "Hassan", "Irene", "James", "Kevin", "Lucy", "Mercy", "Nelson",
               "Olive", "Peter", "Rose", "Samuel", "Tabitha", "Victor"]
LAST_NAMES = ["Otieno", "Wanjiru", "Mwangi", "Achieng", "Kamau", "Njeri", "Ochieng",
              "Mutua", "Wafula", "Chebet", "Kiptoo", "Akinyi", "Odhiambo", "Muthoni",
              "Barasa"]
MESSAGES = ["", "", "Is breakfast included?", "We will arrive late in the evening.",
            "Celebrating an anniversary.", "Need a quiet room.", "Travelling with a toddler."]

# Where enquiries come from, and how often (percent).
SOURCE_WEIGHTS = [
    ("weekend_offer", 30), ("honeymoon_package", 18), ("whatsapp_broadcast", 14),
    ("qr_poster", 8), ("tiktok_clips", 6), ("direct", 12), ("unknown", 4),
    ("phone", 5), ("walk_in", 3),
]

# The status steps an enquiry passed through to reach its final status.
PATHS = {
    S.NEW: [],
    S.CONTACTED: [S.CONTACTED],
    S.PENDING_GUEST: [S.CONTACTED, S.PENDING_GUEST],
    S.RESERVATION_PENDING: [S.CONTACTED, S.RESERVATION_PENDING],
    S.CONFIRMED: [S.CONTACTED, S.RESERVATION_PENDING, S.CONFIRMED],
    S.NOT_CONVERTED: [S.CONTACTED, S.NOT_CONVERTED],
    S.CANCELLED: [S.CONTACTED, S.RESERVATION_PENDING, S.CANCELLED],
}

NOTES = {
    S.CONTACTED: ["Called the guest and shared room options.",
                  "Sent details on WhatsApp, waiting for a reply."],
    S.PENDING_GUEST: ["Guest will confirm after checking with family."],
    S.RESERVATION_PENDING: ["Guest wants to proceed. Pending reservation created."],
    S.CONFIRMED: ["Confirmed by the manager after checking availability."],
    S.NOT_CONVERTED: ["Guest decided not to proceed."],
    S.CANCELLED: ["Guest cancelled the request."],
}

REASONS = {
    S.NOT_CONVERTED: ["Chose another hotel", "Dates not available", "No reply from guest"],
    S.CANCELLED: ["Guest changed plans", "Travel postponed"],
}


def pick_status(rng, age_days):
    """Recent enquiries are mostly open; older ones are mostly resolved."""
    if age_days <= 2:
        options = [(S.NEW, 70), (S.CONTACTED, 30)]
    elif age_days <= 10:
        options = [(S.NEW, 15), (S.CONTACTED, 30), (S.PENDING_GUEST, 20),
                   (S.RESERVATION_PENDING, 15), (S.CONFIRMED, 10), (S.NOT_CONVERTED, 10)]
    else:
        options = [(S.NEW, 4), (S.CONTACTED, 8), (S.PENDING_GUEST, 8),
                   (S.RESERVATION_PENDING, 5), (S.CONFIRMED, 35),
                   (S.NOT_CONVERTED, 30), (S.CANCELLED, 10)]
    return rng.choices([o[0] for o in options], [o[1] for o in options])[0]


class Command(BaseCommand):
    help = "Create sample demo data: rooms, campaigns, enquiries, reservations and two demo staff users."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Delete existing sample enquiries and reservations first.")
        parser.add_argument("--count", type=int, default=60,
                            help="How many sample enquiries to create (default 60).")

    def make_user(self, username, first_name, group):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username, defaults={"first_name": first_name}
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        user.groups.add(group)
        return user

    def attribution(self, key, campaigns, rng):
        web = Enquiry.EntryChannel.WEB_FORM
        if key in campaigns:
            c = campaigns[key]
            return dict(campaign=c, source=c.source, medium=c.medium, campaign_raw=key,
                        landing_page=c.landing_path, entry_channel=web)
        if key == "direct":
            return dict(campaign=None, source="direct", medium="direct", campaign_raw="",
                        landing_page="/promo/", entry_channel=web)
        if key == "unknown":
            return dict(campaign=None, source="unknown", medium="unknown",
                        campaign_raw=rng.choice(["weekend-offer", "spring_sale", "ig"]),
                        landing_page="/promo/", entry_channel=web)
        channel = (Enquiry.EntryChannel.PHONE if key == "phone"
                   else Enquiry.EntryChannel.WALK_IN)
        return dict(campaign=None, source=key, medium="staff_entered", campaign_raw="",
                    landing_page="", entry_channel=channel)

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Reservation.objects.filter(is_sample=True).delete()
            Enquiry.objects.filter(is_sample=True).delete()
        elif Enquiry.objects.filter(is_sample=True).exists():
            raise CommandError("Sample data already exists. Run again with --reset to replace it.")

        rng = random.Random(42)
        now = timezone.now()

        reception_group, _ = Group.objects.get_or_create(name="Reception")
        manager_group, _ = Group.objects.get_or_create(name="Manager")
        reception = self.make_user("reception", "Reception", reception_group)
        manager = self.make_user("manager", "Manager", manager_group)

        rooms = []
        for order, (name, capacity, description) in enumerate(ROOMS, start=1):
            room, _ = RoomType.objects.update_or_create(
                name=name,
                defaults={"capacity": capacity, "description": description,
                          "display_order": order, "is_active": True, "is_sample": True},
            )
            rooms.append(room)

        campaigns = {}
        for name, code, source, medium, headline, offer in CAMPAIGNS:
            campaign, _ = Campaign.objects.update_or_create(
                code=code,
                defaults={"name": name, "source": source, "medium": medium,
                          "headline": headline, "offer_text": offer,
                          "created_by": manager, "is_active": True, "is_sample": True},
            )
            campaigns[code] = campaign

        keys = [k for k, _ in SOURCE_WEIGHTS]
        weights = [w for _, w in SOURCE_WEIGHTS]
        reservation_count = 0

        for _ in range(options["count"]):
            age = rng.random() ** 1.3 * 45
            created = now - timedelta(days=age, minutes=rng.randint(1, 600))
            attrs = self.attribution(rng.choices(keys, weights)[0], campaigns, rng)
            room = rng.choice(rooms) if rng.random() < 0.75 else None
            check_in = (created + timedelta(days=rng.randint(7, 60))).date()
            check_out = check_in + timedelta(days=rng.choice([1, 2, 2, 3, 3, 4, 5]))
            final = pick_status(rng, age)

            enquiry = Enquiry.objects.create(
                guest_name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                phone=f"+254000{rng.randint(0, 999999):06d}",
                preferred_contact=rng.choice(Enquiry.PreferredContact.values),
                requested_check_in=check_in,
                requested_check_out=check_out,
                guest_count=rng.randint(1, room.capacity if room else 4),
                room_type=room,
                message=rng.choice(MESSAGES),
                status=final,
                is_sample=True,
                **attrs,
            )

            # Status history, with timestamps spread after the enquiry was created.
            timeline = [(None, S.NEW, created)]
            previous, moment = S.NEW, created
            for step in PATHS[final]:
                moment = min(
                    moment + timedelta(hours=rng.randint(1, 30), minutes=rng.randint(0, 59)),
                    now - timedelta(minutes=1),
                )
                timeline.append((previous, step, moment))
                previous = step

            reservation_time = None
            for before, step, when in timeline:
                if step is S.NEW:
                    changed_by = None
                else:
                    changed_by = manager if step is S.CONFIRMED else reception
                reason = rng.choice(REASONS[step]) if step in REASONS else ""
                change = StatusChange.objects.create(
                    enquiry=enquiry,
                    from_status=before.value if before else "",
                    to_status=step.value,
                    changed_by=changed_by,
                    reason=reason,
                )
                StatusChange.objects.filter(pk=change.pk).update(changed_at=when)

                if step is not S.NEW:
                    follow_up = None
                    if step is final and final in (S.CONTACTED, S.PENDING_GUEST):
                        follow_up = when + timedelta(days=2)
                    note = EnquiryNote.objects.create(
                        enquiry=enquiry,
                        author=changed_by,
                        note=rng.choice(NOTES[step]),
                        next_follow_up_at=follow_up,
                    )
                    EnquiryNote.objects.filter(pk=note.pk).update(created_at=when)
                if step is S.RESERVATION_PENDING:
                    reservation_time = when

            if final in (S.RESERVATION_PENDING, S.CONFIRMED, S.CANCELLED):
                last_when = timeline[-1][2]
                status = {
                    S.RESERVATION_PENDING: Reservation.Status.PENDING,
                    S.CONFIRMED: Reservation.Status.CONFIRMED,
                    S.CANCELLED: Reservation.Status.CANCELLED,
                }[final]
                reservation = Reservation.objects.create(
                    enquiry=enquiry,
                    room_type=room or rooms[0],
                    check_in=check_in,
                    check_out=check_out,
                    guest_count=enquiry.guest_count,
                    status=status,
                    created_by=reception,
                    confirmed_by=manager if final is S.CONFIRMED else None,
                    confirmed_at=last_when if final is S.CONFIRMED else None,
                    cancellation_reason=rng.choice(REASONS[S.CANCELLED]) if final is S.CANCELLED else "",
                    is_sample=True,
                )
                Reservation.objects.filter(pk=reservation.pk).update(created_at=reservation_time)
                reservation_count += 1

            Enquiry.objects.filter(pk=enquiry.pk).update(
                created_at=created, updated_at=timeline[-1][2]
            )

        self.stdout.write(self.style.SUCCESS(
            f"Created {options['count']} enquiries, {reservation_count} reservations, "
            f"{len(rooms)} room types and {len(campaigns)} campaigns."
        ))
        self.stdout.write(
            f"Demo staff logins: reception / {DEMO_PASSWORD} and manager / {DEMO_PASSWORD}"
        )
