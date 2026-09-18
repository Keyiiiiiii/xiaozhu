def has_perm(user, code):
    """Return True if the user's role includes the given permission code."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    role = getattr(user, "role", None)
    if role is None:
        return False
    return role.permissions.filter(code=code).exists()
