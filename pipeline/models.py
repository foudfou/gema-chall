"""Data models for the pipeline."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ISRC format: 2 letter country + 3 char registrant + 2 digit year + 5 digit designation
ISRC_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$")


class RawPlayEvent(BaseModel):
    """Raw play event as read from CSV."""

    timestamp: datetime
    isrc_code: str
    station_id: str
    duration_seconds: int = Field(ge=0)
    listener_count: int = Field(ge=0)

    @field_validator("isrc_code")
    @classmethod
    def validate_isrc(cls, v: str) -> str:
        if not ISRC_PATTERN.match(v):
            raise ValueError(f"Invalid ISRC format: {v}")
        return v


class WorkDetails(BaseModel):
    """Work details from the Work-Catalog-API."""

    artist: str
    title: str
    rights_holder: str


class EnrichedPlayEvent(BaseModel):
    """Play event after enrichment and transformation."""

    timestamp: datetime
    isrc_code: str
    station_id: str
    duration_seconds: int
    listener_count: int
    artist: str
    title: str
    rights_holder: str
    listened_seconds: int  # duration_seconds * listener_count
