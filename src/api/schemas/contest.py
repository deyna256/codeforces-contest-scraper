"""Pydantic schemas for contest API endpoints."""

from pydantic import BaseModel


class ContestRequest(BaseModel):
    """Request for contest information."""

    url: str


class ContestProblemResponse(BaseModel):
    """Response containing problem information within a contest."""

    contest_id: str
    id: str
    title: str
    statement: str | None = None
    rating: int | None = None
    tags: list[str]
    time_limit: str | None = None
    memory_limit: str | None = None
    explanation: str | None = None

    class Config:
        from_attributes = True


class ContestResponse(BaseModel):
    """Response containing contest information."""

    contest_id: str
    title: str
    problems: list[ContestProblemResponse]
    editorials: list[str]

    class Config:
        from_attributes = True
