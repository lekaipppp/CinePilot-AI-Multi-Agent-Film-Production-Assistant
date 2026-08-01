"""
Shared / common Pydantic schemas used across multiple routers.
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list wrapper."""
    items: List[T]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    """Simple message envelope for operations that return no entity."""
    message: str


class ErrorDetail(BaseModel):
    """Structured error detail returned in 4xx / 5xx responses."""
    code: str
    message: str
    detail: Optional[Any] = None
