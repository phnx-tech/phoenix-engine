"""URL classification data model."""

from __future__ import annotations

from pydantic import BaseModel, Field


class URLClassification(BaseModel):
    """Classification of a URL into a platform and content type."""

    url: str = Field(..., description="Normalized source URL.")
    platform: str = Field(..., description="Platform identifier (e.g., 'x', 'instagram').")
    content_type: str = Field(
        default="post",
        description="Type of content (e.g., 'post', 'profile', 'video').",
    )


__all__ = ["URLClassification"]
