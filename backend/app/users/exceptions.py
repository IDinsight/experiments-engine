class UserNotFoundError(Exception):
    """Exception raised when a user is not found in the database."""


class UserAlreadyExistsError(Exception):
    """Exception raised when a user already exists in the database."""
