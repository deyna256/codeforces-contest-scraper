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

    class Config:
        from_attributes = True