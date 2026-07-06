"""CSV ingestion with chunked reading."""

from pathlib import Path
from typing import Iterator

import pandas as pd
import structlog

log = structlog.get_logger()

DEFAULT_CHUNK_SIZE = 10_000


def read_csv_chunks(
    file_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Iterator[pd.DataFrame]:
    """
    Read a CSV file in chunks.

    Yields DataFrames of chunk_size rows each.
    """
    file_path = Path(file_path)
    log.info("ingestion_started", file=str(file_path), chunk_size=chunk_size)

    for chunk_num, chunk in enumerate(
        pd.read_csv(file_path, chunksize=chunk_size)
    ):
        log.debug("chunk_read", chunk_num=chunk_num, rows=len(chunk))
        yield chunk

    log.info("ingestion_completed", file=str(file_path))
