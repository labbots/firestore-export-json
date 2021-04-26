class BaseError(Exception):
    """Base class for other exceptions"""
    pass


class ValidationError(BaseError):
    """Raised when validation error occurs"""
    pass
