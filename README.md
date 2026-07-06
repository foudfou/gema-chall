# GEMA Music Usage Data Pipeline

A data processing pipeline for radio station play logs.

## Usage

```bash
# Install dependencies
uv sync --all-extras

# Run pipeline
uv run python main.py data/sample.csv
# Check results
sqlite3 data/play_events.db .dump

# Run tests
uv run pytest -v
```

## Implementation

The intent of current implementation is to demonstrate modular code
(`pipeline/`) used from a CLI (`main.py`). The current processor
(`pipeline/processor.py`) is meant *as an illustration*: synchronous et
sequential.

Simplifications include:

| Current implementation              | Production                                                |
|-------------------------------------|-----------------------------------------------------------|
| CSV files provided via CLI argument | Watch directory, S3 trigger, or API upload                |
| Mocked Work-Catalog-API             | HTTP client or lookup on existing database table / cache  |
| SQLite for simplicity               | PostgreSQL, Data Warehouse                                |
| Single-process execution            | Concurrency or task queue (Celery) for horizontal scaling |

A distributed system (workers orchestrated around a queue system) might not be
the best answer since the pipeline is quite linear and resilience is best
handled by data processing platforms. A real-world production deployment
probably uses batch jobs scheduled onto a data processing infrastructure,
something like **Airflow + Spark**.

Considerations:

- **Efficiency**:
  - Chunked reading (implemented): Files are read in configurable chunks
    (default 10k rows) to bound memory usage for 100MB+ files
  - Batch DB writes: Processed records are inserted in batches via
    `pandas.to_sql()` rather than row-by-row
  - Batch enrichment API: Instead of one API call per ISRC, batch multiple ISRCs per request
  - Parallel processing (not implemented yet): Process multiple chunks
    concurrently with `concurrent.futures` or Celery workers
  - Connection pooling (not implemented yet): Use SQLAlchemy with connection
    pooling for high-throughput DB access
  - Async I/O (not implemented yet): Use `aiohttp` + `asyncpg` for non-blocking I/O

- **Error Handling**
  - Structured logging: Logs with full context can be shipped to
    ELK/Datadog/etc. for alerting and analysis. On validation error, the
    pipeline continues.
  - Retry with backoff: Transient failures in enrichment API and DB writes are
    retried with exponential backoff (`tenacity`). On a production system
    failed retries would be published with full context to a Dead Letter Queue
    for manual review or automated retry

- **Idempotency**: we need to ingest each row exactly once. The current
  implementation creates duplicates. We could use `timestamp + isrc_code +
  station_id` as a reasonable key. Re-sent files and updates are a legitimate
  use case (business decision). We could also track processed files to avoid
  re-processing of re-sent files.
