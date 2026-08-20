from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    environment: str
    database: str = "connected"
    ai_provider: str
