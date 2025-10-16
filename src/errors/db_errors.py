class UserAlreadyExistsError(Exception):
    """Raised when attempting to create a user that already exists."""
    pass


class UserNotFoundError(Exception):
    """Raised when a user is not found."""
    pass