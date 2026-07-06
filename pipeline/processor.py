"""Core processing logic: validate, enrich, transform."""

import pandas as pd
import structlog
from pydantic import ValidationError

from pipeline.enrichment import WorkCatalogClient
from pipeline.models import EnrichedPlayEvent, RawPlayEvent, WorkDetails

log = structlog.get_logger()


class Processor:
    """Processes raw play events into enriched events."""

    def __init__(self, catalog_client: WorkCatalogClient):
        self.catalog_client = catalog_client

    def validate_row(self, row: dict, row_index: int) -> RawPlayEvent | None:
        """Validate a single row. Returns RawPlayEvent or None if invalid."""
        try:
            return RawPlayEvent(**row)
        except ValidationError as e:
            log.error(
                "validation_failed",
                row_index=row_index,
                errors=e.errors(),
                raw_data=row,
            )
            return None

    def transform(
        self, event: RawPlayEvent, work_details: WorkDetails
    ) -> EnrichedPlayEvent:
        """Transform a validated event with work details into enriched event."""
        return EnrichedPlayEvent(
            timestamp=event.timestamp,
            isrc_code=event.isrc_code,
            station_id=event.station_id,
            duration_seconds=event.duration_seconds,
            listener_count=event.listener_count,
            artist=work_details.artist,
            title=work_details.title,
            rights_holder=work_details.rights_holder,
            listened_seconds=event.duration_seconds * event.listener_count,
        )

    def process_dataframe(self, df: pd.DataFrame) -> list[EnrichedPlayEvent]:
        """
        Process a DataFrame chunk.

        1. Validate all rows
        2. Batch enrich (one API call for all unique ISRCs)
        3. Transform each valid event
        """
        # Validate
        validated: list[tuple[int, RawPlayEvent]] = []
        for row_num, (_, row) in enumerate(df.iterrows()):
            event = self.validate_row(row.to_dict(), row_num)
            if event is not None:
                validated.append((row_num, event))

        if not validated:
            return []

        # Batch enrich
        unique_isrcs = list({event.isrc_code for _, event in validated})
        try:
            work_details_map = self.catalog_client.get_work_details_batch(unique_isrcs)
        except Exception as e:
            log.error("batch_enrichment_failed", error=str(e), isrc_count=len(unique_isrcs))
            return []

        # Transform
        results: list[EnrichedPlayEvent] = []
        for row_num, event in validated:
            work_details = work_details_map.get(event.isrc_code)
            if work_details is None:
                log.error(
                    "enrichment_missing",
                    row_index=row_num,
                    isrc_code=event.isrc_code,
                )
                continue
            results.append(self.transform(event, work_details))

        return results
