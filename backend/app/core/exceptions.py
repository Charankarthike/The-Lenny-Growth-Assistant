"""
Custom exceptions for the application
"""


class LennyAssistantException(Exception):
    """Base exception for all application errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(LennyAssistantException):
    """Database-related errors"""
    pass


class OpenAIError(LennyAssistantException):
    """OpenAI API errors"""
    pass


class RAGError(LennyAssistantException):
    """RAG retrieval errors"""
    pass


class ConfigurationError(LennyAssistantException):
    """Configuration errors"""
    pass


class ValidationError(LennyAssistantException):
    """Data validation errors"""
    pass
