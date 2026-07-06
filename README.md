# GEMA Music Usage Data Pipeline

A data processing pipeline for radio station play logs.

## Usage

```bash
# Install dependencies
uv sync --all-extras

# Run pipeline
uv run python main.py data/sample.csv

# Run tests
uv run pytest -v
```

## Implementation

The intent of current implementation is to demonstrate modular code
(`pipeline/`) used from a CLI (`main.py`). The current processor
(`pipeline/processor.py`) is meant *as an illustration*: synchronous et
sequential.

A production deployment would decouple these fonctions into distributed
processors orchestrated around a queue system in order to provide flexibility
and resilience.

TODO production schema.
