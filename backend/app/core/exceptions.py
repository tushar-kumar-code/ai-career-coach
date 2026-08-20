from fastapi import HTTPException, status


class AICareerCoachException(Exception):
    """Base exception class for AI Career Coach application."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AIProviderException(AICareerCoachException):
    """Exception raised when AI service provider fails."""
    pass


class DocumentParseException(AICareerCoachException):
    """Exception raised when resume/document parsing fails."""
    pass


class ResourceNotFoundException(AICareerCoachException):
    """Exception raised when a requested resource is not found."""
    pass
