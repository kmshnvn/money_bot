import enum


class UserRole(enum.IntEnum):
    """You can change these roles as you want."""

    USER = 0
    ADMINISTRATOR = 1
    VIEWER = 2
