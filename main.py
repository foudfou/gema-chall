"""CLI entry point for the GEMA pipeline."""

import argparse
import logging
import sys
import time
from pathlib import Path

import structlog

from pipeline.database import SqliteDatabase
from pipeline.enrichment import FakeWorkCatalogClient
from pipeline.ingest import read_csv_chunks
from pipeline.processor import Processor


def configure_logging(verbose: bool = False) -> None:
    """Configure structlog for JSON output."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if verbose else logging.INFO
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Process radio station play logs"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to input CSV file",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default="data/play_events.db",
        help="Path to SQLite database (default: data/play_events.db)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10_000,
        help="Number of rows to process at a time (default: 10000)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    configure_logging(args.verbose)
    log = structlog.get_logger()

    if not args.input_file.exists():
        log.error("file_not_found", file=str(args.input_file))
        return 1

    log.info(
        "pipeline_started",
        input_file=str(args.input_file),
        db=str(args.db),
        chunk_size=args.chunk_size,
    )

    start_time = time.perf_counter()
    processor = Processor(catalog_client=FakeWorkCatalogClient())
    database = SqliteDatabase(args.db)

    total_processed = 0
    total_stored = 0

    for chunk in read_csv_chunks(args.input_file, args.chunk_size):
        events = list(processor.process_dataframe(chunk))
        total_processed += len(chunk)
        total_stored += database.store_batch(events)

    elapsed = time.perf_counter() - start_time

    log.info(
        "pipeline_completed",
        total_rows=total_processed,
        stored=total_stored,
        failed=total_processed - total_stored,
        elapsed_seconds=round(elapsed, 3),
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
