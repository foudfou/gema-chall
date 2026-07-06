"""Core processing logic: validate, enrich, transform."""

from typing import Iterator

import pandas as pd
import structlog
from pydantic import ValidationError

from pipeline.enrichment import WorkCatalogClient
from pipeline.models import EnrichedPlayEvent, RawPlayEvent

log = structlog.get_logger()


class Processor:
    """Processes raw play events into enriched events."""

    def __init__(self, catalog_client: WorkCatalogClient):
        self.catalog_client = catalog_client

    def process_row(self, row: dict, row_index: int) -> EnrichedPlayEvent | None:
        """
        Process a single row: validate, enrich, transform.

        Returns EnrichedPlayEvent on success, None on failure (logged).
        """
        # Validate
        try:
            raw_event = RawPlayEvent(**row)
        except ValidationError as e:
            log.error(
                "validation_failed",
                row_index=row_index,
                errors=e.errors(),
                raw_data=row,
            )
            return None

        # Enrich
        try:
            work_details = self.catalog_client.get_work_details(raw_event.isrc_code)
        except Exception as e:
            log.error(
                "enrichment_failed",
                row_index=row_index,
                isrc_code=raw_event.isrc_code,
                error=str(e),
            )
            return None

        # Transform
        listened_seconds = raw_event.duration_seconds * raw_event.listener_count

        return EnrichedPlayEvent(
            timestamp=raw_event.timestamp,
            isrc_code=raw_event.isrc_code,
            station_id=raw_event.station_id,
            duration_seconds=raw_event.duration_seconds,
            listener_count=raw_event.listener_count,
            artist=work_details.artist,
            title=work_details.title,
            rights_holder=work_details.rights_holder,
            listened_seconds=listened_seconds,
        )

    def process_dataframe(self, df: pd.DataFrame) -> Iterator[EnrichedPlayEvent]:
        """Process a DataFrame chunk, yielding enriched events."""
        for row_num, (_, row) in enumerate(df.iterrows()):
            result = self.process_row(row.to_dict(), row_num)
            if result is not None:
                yield result
