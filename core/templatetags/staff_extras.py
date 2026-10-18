from django import template

register = template.Library()


@register.filter
def short_name(value):
    """'David Ochieng' becomes 'David O.'; a single name is left alone."""
    parts = str(value or "").split()
    if len(parts) < 2:
        return " ".join(parts)
    return f"{parts[0]} {parts[1][0].upper()}."
