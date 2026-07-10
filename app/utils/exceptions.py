"""
Custom exception types used across the app.
"""

class AppException(Exception):
    """Base exception for all app-level errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UnsupportedFileTypeError(AppException):
    def __init__(self, message: str = "Unsupported file type."):
        super().__init__(message, status_code=415)


class FileTooLargeError(AppException):
    def __init__(self, message: str = "File exceeds maximum allowed size."):
        super().__init__(message, status_code=413)


class CollectionNotFoundError(AppException):
    def __init__(self, message: str = "Collection not found."):
        super().__init__(message, status_code=404)


class RetrievalError(AppException):
    def __init__(self, message: str = "Failed to retrieve documents."):
        super().__init__(message, status_code=500)


class LLMGenerationError(AppException):
    def __init__(self, message: str = "LLM failed to generate a response."):
        super().__init__(message, status_code=502)
