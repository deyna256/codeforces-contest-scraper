"""Pydantic schemas for editorial API endpoints."""

from pydantic import BaseModel


class EditorialResponse(BaseModel):
    """Response containing editorial analysis for a specific problem."""

    problem_id: str
    analysis_text: str

    class Config:
        from_attributes = True


class ContestEditorialResponse(BaseModel):
    """Response containing all editorial analyses for a contest."""

    contest_id: str
    editorials: list[EditorialResponse]

    class Config:
        from_attributes = True
