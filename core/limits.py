MAX_ONLINE_GROUP = 12


def group_size_error(count):
    """Message for a group too large to enquire about online, else None."""
    if count and count > MAX_ONLINE_GROUP:
        return (
            f"For groups of more than {MAX_ONLINE_GROUP} we arrange rooms personally. "
            "Please call or WhatsApp us and we will sort it out."
        )
    return None
