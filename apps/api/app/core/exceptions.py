"""Custom exception classes for the application."""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(detail=f"{resource} not found", status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    """Resource conflict (e.g., duplicate email)."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class UnauthorizedException(AppException):
    """Authentication required."""

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    """Insufficient permissions."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class ValidationException(AppException):
    """Input validation error."""

    def __init__(self, detail: str = "Validation error"):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
