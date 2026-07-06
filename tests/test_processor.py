"""Tests for the processor module."""

from pipeline.enrichment import FakeWorkCatalogClient
from pipeline.processor import Processor

FAKE_CLIENT = FakeWorkCatalogClient()


class TestProcessor:
    """Test the processor logic."""

    def test_process_valid_row(self):
        """Valid row should be processed and transformed."""
        processor = Processor(FAKE_CLIENT)
        row = {
            "timestamp": "2026-01-15T08:30:00Z",
            "isrc_code": "USRC17607839",
            "station_id": "RADIO_WDR",
            "duration_seconds": 245,
            "listener_count": 150000,
        }

        result = processor.process_row(row, row_index=0)

        assert result is not None
        assert result.listened_seconds == 245 * 150000
        assert result.artist == "Taylor Swift"

    def test_process_invalid_row_returns_none(self):
        """Invalid row should return None (not crash)."""
        processor = Processor(FAKE_CLIENT)
        row = {
            "timestamp": "2026-01-15T08:30:00Z",
            "isrc_code": "BAD_ISRC",
            "station_id": "RADIO_WDR",
            "duration_seconds": 245,
            "listener_count": 150000,
        }

        result = processor.process_row(row, row_index=0)

        assert result is None

    def test_listened_seconds_calculation(self):
        """Verify listened_seconds = duration * listeners."""
        processor = Processor(FAKE_CLIENT)
        row = {
            "timestamp": "2026-01-15T08:30:00Z",
            "isrc_code": "DEFR32400001",
            "station_id": "RADIO_WDR",
            "duration_seconds": 180,
            "listener_count": 100000,
        }

        result = processor.process_row(row, row_index=0)

        assert result is not None
        assert result.listened_seconds == 18_000_000
