"""Pydantic schemas for problem API endpoints."""

from pydantic import BaseModel


class ProblemRequest(BaseModel):
    """Request for problem information."""

    url: str


class ProblemResponse(BaseModel):
    """Response containing problem information."""

    statement: str
    tags: list[str]
    rating: int | None = None
    contest_id: str
    id: str
    url: str  # Original URL
    description: str | None = None  # Full problem statement
    time_limit: str | None = None  # Time limit (e.g., "2 seconds")
    memory_limit: str | None = None  # Memory limit (e.g., "256 megabytes")

    class Config:
        from_attributes = True
