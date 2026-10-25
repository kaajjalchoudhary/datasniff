"""Turn a file path (or glob) into a DuckDB table function call."""

from __future__ import annotations

CSV_SUFFIXES = (".csv", ".tsv", ".txt", ".csv.gz", ".tsv.gz")
PARQUET_SUFFIXES = (".parquet", ".pq")
JSON_SUFFIXES = (".json", ".jsonl", ".ndjson", ".json.gz", ".jsonl.gz")


class UnsupportedFormat(ValueError):
    pass


def _literal(path: str) -> str:
    return "'" + path.replace("'", "''") + "'"


def source_sql(path: str) -> str:
    """Return a DuckDB expression that reads ``path``. Globs such as ``data/*.parquet`` work too."""
    lower = path.lower()
    lit = _literal(path)
    if lower.endswith(PARQUET_SUFFIXES):
        return f"read_parquet({lit})"
    if lower.endswith(JSON_SUFFIXES):
        return f"read_json_auto({lit})"
    if lower.endswith(CSV_SUFFIXES):
        # sample_size=-1 scans the whole file for type detection, avoiding mid-file cast errors.
        return f"read_csv_auto({lit}, sample_size=-1)"
    raise UnsupportedFormat(
        f"Don't know how to read {path!r}. "
        "Supported: CSV/TSV, Parquet, JSON/NDJSON (optionally .gz)."
    )
