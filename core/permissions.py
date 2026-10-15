from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def user_role(user):
    """Return 'manager', 'reception' or None, based on the user's group."""
    names = set(user.groups.values_list("name", flat=True))
    if "Manager" in names:
        return "manager"
    if "Reception" in names:
        return "reception"
    return None


def role_required(*roles):
    """Require a signed-in user whose role is one of `roles`."""

    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if user_role(request.user) not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
