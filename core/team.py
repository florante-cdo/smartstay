"""Staff account rules, kept apart from the views so they can be tested on their own."""
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import StaffProfile
from core.permissions import user_role
from enquiries.models import Enquiry
from enquiries.services import assign

ROLES = {"reception": "Reception", "manager": "Manager"}
ROLE_GROUPS = r"^(reception|manager)$"
CLOSED = [Enquiry.Status.CONFIRMED, Enquiry.Status.NOT_CONVERTED, Enquiry.Status.CANCELLED]


def _group(role):
    name = ROLES[role]
    return Group.objects.filter(name__iexact=name).first() or Group.objects.create(name=name)


def team_queryset():
    return (
        User.objects.filter(groups__name__iregex=ROLE_GROUPS)
        .distinct()
        .order_by("-is_active", "first_name", "username")
    )


def active_managers():
    return User.objects.filter(is_active=True, groups__name__iregex=r"^manager$").distinct()


def is_last_active_manager(user):
    return (
        user.is_active
        and user_role(user) == "manager"
        and not active_managers().exclude(pk=user.pk).exists()
    )


@transaction.atomic
def create_member(data):
    user = User.objects.create_user(
        username=data["username"],
        email=data.get("email", ""),
        password=data["password"],
        first_name=data["first_name"],
        last_name=data.get("last_name", ""),
    )
    user.groups.add(_group(data["role"]))
    StaffProfile.objects.update_or_create(
        user=user,
        defaults={"phone": data.get("phone", ""), "job_title": data.get("job_title", "")},
    )
    return user


@transaction.atomic
def set_role(user, role, by):
    if role not in ROLES:
        raise ValidationError("Choose Reception or Manager.")
    if user.pk == by.pk:
        raise ValidationError("You cannot change your own role. Ask another Manager.")
    if role != "manager" and is_last_active_manager(user):
        raise ValidationError("There must be at least one active Manager.")
    user.groups.remove(*Group.objects.filter(name__iregex=ROLE_GROUPS))
    user.groups.add(_group(role))


@transaction.atomic
def deactivate(user, by):
    """Switch an account off and release its open enquiries. Returns how many were released."""
    if user.pk == by.pk:
        raise ValidationError("You cannot deactivate your own account.")
    if is_last_active_manager(user):
        raise ValidationError("There must be at least one active Manager.")
    user.is_active = False
    user.save(update_fields=["is_active"])
    released = 0
    for enquiry in Enquiry.objects.filter(assigned_to=user).exclude(status__in=CLOSED):
        assign(enquiry, None, by)
        released += 1
    return released


def reactivate(user):
    user.is_active = True
    user.save(update_fields=["is_active"])
