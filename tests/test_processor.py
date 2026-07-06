"""Tests for the processor module."""

from datetime import datetime, timezone

import pandas as pd

from pipeline.enrichment import FakeWorkCatalogClient
from pipeline.models import RawPlayEvent, WorkDetails
from pipeline.processor import Processor

FAKE_CLIENT = FakeWorkCatalogClient()
TS = datetime(2026, 1, 15, 8, 30, 0, tzinfo=timezone.utc)


class TestValidation:
    """Test row validation."""

    def test_valid_row(self):
        """Valid row should return RawPlayEvent."""
        processor = Processor(FAKE_CLIENT)
        row = {
            "timestamp": "2026-01-15T08:30:00Z",
            "isrc_code": "USRC17607839",
            "station_id": "RADIO_WDR",
            "duration_seconds": 245,
            "listener_count": 150000,
        }

        result = processor.validate_row(row, row_index=0)

        assert result is not None
        assert result.isrc_code == "USRC17607839"

    def test_invalid_row_returns_none(self):
        """Invalid row should return None."""
        processor = Processor(FAKE_CLIENT)
        row = {
            "timestamp": "2026-01-15T08:30:00Z",
            "isrc_code": "BAD_ISRC",
            "station_id": "RADIO_WDR",
            "duration_seconds": 245,
            "listener_count": 150000,
        }

        result = processor.validate_row(row, row_index=0)

        assert result is None


class TestTransform:
    """Test transformation logic."""

    def test_listened_seconds_calculation(self):
        """Verify listened_seconds = duration * listeners."""
        processor = Processor(FAKE_CLIENT)
        event = RawPlayEvent(
            timestamp=TS,
            isrc_code="DEFR32400001",
            station_id="RADIO_WDR",
            duration_seconds=180,
            listener_count=100000,
        )
        work_details = WorkDetails(
            artist="Kraftwerk",
            title="Autobahn",
            rights_holder="Kling Klang",
        )

        result = processor.transform(event, work_details)

        assert result.listened_seconds == 18_000_000
        assert result.artist == "Kraftwerk"


class TestProcessDataframe:
    """Test batch processing."""

    def test_batch_enrichment(self):
        """Process multiple rows with batch enrichment."""
        processor = Processor(FAKE_CLIENT)
        df = pd.DataFrame([
            {
                "timestamp": "2026-01-15T08:30:00Z",
                "isrc_code": "USRC17607839",
                "station_id": "RADIO_WDR",
                "duration_seconds": 245,
                "listener_count": 150000,
            },
            {
                "timestamp": "2026-01-15T08:35:00Z",
                "isrc_code": "DEFR32400001",
                "station_id": "RADIO_WDR",
                "duration_seconds": 180,
                "listener_count": 150000,
            },
        ])

        results = processor.process_dataframe(df)

        assert len(results) == 2
        assert results[0].artist == "Taylor Swift"
        assert results[1].artist == "Kraftwerk"

    def test_skips_invalid_rows(self):
        """Invalid rows should be skipped, valid ones processed."""
        processor = Processor(FAKE_CLIENT)
        df = pd.DataFrame([
            {
                "timestamp": "2026-01-15T08:30:00Z",
                "isrc_code": "USRC17607839",
                "station_id": "RADIO_WDR",
                "duration_seconds": 245,
                "listener_count": 150000,
            },
            {
                "timestamp": "2026-01-15T08:35:00Z",
                "isrc_code": "INVALID_ISRC",
                "station_id": "RADIO_WDR",
                "duration_seconds": 180,
                "listener_count": 150000,
            },
        ])

        results = processor.process_dataframe(df)

        assert len(results) == 1
        assert results[0].artist == "Taylor Swift"
