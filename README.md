# GEMA Musik-Nutzungsdaten-Pipeline

Eine Datenverarbeitungs-Pipeline für Radiosender-Abspiellogs.

## Verwendung

```bash
# Dependencies installieren
uv sync --all-extras

# Pipeline ausführen
uv run python main.py data/sample.csv
# Ergebnisse prüfen
sqlite3 data/play_events.db .dump

# Tests ausführen
uv run pytest -v
```

## Implementierung

Die aktuelle Implementierung soll modularen Code (`pipeline/`) demonstrieren,
der von einer CLI (`main.py`) verwendet wird. Der aktuelle Processor
(`pipeline/processor.py`) ist *als Illustration* gedacht: synchron und
sequentiell.

Vereinfachungen umfassen:

| Aktuelle Implementierung              | Production                                                     |
|---------------------------------------|----------------------------------------------------------------|
| CSV-Dateien über CLI-Argument         | Watch Directory, S3 Trigger, oder API Upload                   |
| Gemockte Work-Catalog-API             | HTTP Client oder Lookup auf bestehender Datenbanktabelle/Cache |
| SQLite der Einfachheit halber         | PostgreSQL, Data Warehouse                                     |
| Single-Process-Ausführung             | Concurrency oder Task Queue (Celery) für horizontale Skalierung |

Ein verteiltes System (Worker orchestriert um ein Queue-System) ist
möglicherweise nicht die beste Lösung, da die Pipeline recht linear ist und
Resilience am besten von Datenverarbeitungsplattformen gehandhabt wird. Ein
realer Production-Einsatz verwendet wahrscheinlich Batch Jobs, die auf einer
Datenverarbeitungsinfrastruktur scheduled werden, etwa **Airflow + Spark**.

Überlegungen:

- **Effizienz**:
  - Chunked Reading (implementiert): Dateien werden in konfigurierbaren Chunks
    gelesen (Default 10k Zeilen), um den Speicherverbrauch bei 100MB+ Dateien
    zu begrenzen
  - Batch DB Writes: Verarbeitete Records werden in Batches über
    `pandas.to_sql()` eingefügt, anstatt Row-by-Row
  - Batch Enrichment API: Anstatt eines API Calls pro ISRC werden mehrere ISRCs
    pro Request gebündelt
  - Parallel Processing (noch nicht implementiert): Mehrere Chunks gleichzeitig
    mit `concurrent.futures` oder Celery Workers verarbeiten
  - Connection Pooling (noch nicht implementiert): SQLAlchemy mit Connection
    Pooling für High-Throughput DB Access verwenden
  - Async I/O (noch nicht implementiert): `aiohttp` + `asyncpg` für
    Non-Blocking I/O verwenden

- **Error Handling**
  - Structured Logging: Logs mit vollständigem Context können an
    ELK/Datadog/etc. für Alerting und Analyse gesendet werden. Bei
    Validation Errors läuft die Pipeline weiter.
  - Retry mit Backoff: Transient Failures bei der Enrichment API und DB Writes
    werden mit Exponential Backoff wiederholt (`tenacity`). In einem
    Production-System würden fehlgeschlagene Retries mit vollständigem Context
    in eine Dead Letter Queue publiziert, für manuelle Review oder
    automatisierten Retry

- **Idempotency**: Jede Zeile muss genau einmal verarbeitet werden. Die aktuelle
  Implementierung erzeugt Duplikate. `timestamp + isrc_code + station_id` wäre
  ein sinnvoller Key. Erneut gesendete Dateien und Updates sind ein legitimer
  Use Case (Business-Entscheidung). Verarbeitete Dateien könnten auch getrackt
  werden, um Re-Processing von wiederholten Dateien zu vermeiden.
