"""Tests for the models module."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from pipeline.models import RawPlayEvent

TS = datetime(2026, 1, 15, 8, 30, 0, tzinfo=timezone.utc)


class TestRawPlayEventValidation:
    """Test validation of raw play events."""

    def test_valid_event(self):
        """Valid event should parse successfully."""
        event = RawPlayEvent(
            timestamp=TS,
            isrc_code="USRC17607839",
            station_id="RADIO_WDR",
            duration_seconds=245,
            listener_count=150000,
        )
        assert event.isrc_code == "USRC17607839"
        assert event.duration_seconds == 245

    def test_invalid_isrc_format(self):
        """Invalid ISRC should raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            RawPlayEvent(
                timestamp=TS,
                isrc_code="INVALID",
                station_id="RADIO_WDR",
                duration_seconds=245,
                listener_count=150000,
            )
        assert "Invalid ISRC format" in str(exc_info.value)

    def test_invalid_timestamp(self):
        """Invalid timestamp should raise validation error."""
        with pytest.raises(ValidationError):
            RawPlayEvent(
                timestamp="not-a-date",  # type: ignore[arg-type]
                isrc_code="USRC17607839",
                station_id="RADIO_WDR",
                duration_seconds=245,
                listener_count=150000,
            )

    def test_negative_duration(self):
        """Negative duration should raise validation error."""
        with pytest.raises(ValidationError):
            RawPlayEvent(
                timestamp=TS,
                isrc_code="USRC17607839",
                station_id="RADIO_WDR",
                duration_seconds=-1,
                listener_count=150000,
            )
