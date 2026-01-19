"""Pydantic schemas for problem API endpoints."""

from pydantic import BaseModel


class ProblemRequest(BaseModel):
    """Request for problem information."""

    url: str


class ProblemResponse(BaseModel):
    """Response containing problem information."""

    contest_id: str
    id: str
    statement: str
    description: str | None = None  # Full problem statement
    time_limit: str | None = None  # Time limit (e.g., "2 seconds")
    memory_limit: str | None = None  # Memory limit (e.g., "256 megabytes")
    rating: int | None = None
    tags: list[str]
    url: str  # Original URL

    class Config:
        from_attributes = True
