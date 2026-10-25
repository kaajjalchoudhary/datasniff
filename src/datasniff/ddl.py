"""Generate CREATE TABLE statements for common warehouses from the inferred schema."""

from __future__ import annotations

import re

from datasniff.profile import TableProfile

DIALECTS = ("duckdb", "postgres", "bigquery", "snowflake")

_INT = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "UTINYINT", "USMALLINT", "UINTEGER")


def map_type(dtype: str, dialect: str) -> str:
    t = dtype.upper()
    if dialect == "duckdb":
        return dtype
    decimal = re.match(r"DECIMAL\((\d+),\s*(\d+)\)", t)
    if t in _INT or t in ("UBIGINT", "HUGEINT", "UHUGEINT"):
        big = t in ("BIGINT", "UBIGINT", "HUGEINT", "UHUGEINT", "UINTEGER")
        return {
            "postgres": "BIGINT" if big else "INTEGER",
            "bigquery": "INT64",
            "snowflake": "NUMBER(38,0)",
        }[dialect]
    if t in ("DOUBLE", "FLOAT", "REAL"):
        return {"postgres": "DOUBLE PRECISION", "bigquery": "FLOAT64", "snowflake": "FLOAT"}[
            dialect
        ]
    if decimal:
        p, s = decimal.groups()
        return {
            "postgres": f"NUMERIC({p},{s})",
            "bigquery": f"NUMERIC({p},{s})",
            "snowflake": f"NUMBER({p},{s})",
        }[dialect]
    if t == "BOOLEAN":
        return {"postgres": "BOOLEAN", "bigquery": "BOOL", "snowflake": "BOOLEAN"}[dialect]
    if t == "DATE":
        return "DATE"
    if t in ("TIMESTAMP WITH TIME ZONE", "TIMESTAMPTZ"):
        return {"postgres": "TIMESTAMPTZ", "bigquery": "TIMESTAMP", "snowflake": "TIMESTAMP_TZ"}[
            dialect
        ]
    if t.startswith("TIMESTAMP"):
        return {"postgres": "TIMESTAMP", "bigquery": "DATETIME", "snowflake": "TIMESTAMP_NTZ"}[
            dialect
        ]
    if t == "TIME":
        return "TIME"
    if t == "VARCHAR":
        return {"postgres": "TEXT", "bigquery": "STRING", "snowflake": "VARCHAR"}[dialect]
    # Nested / exotic types fall back to semi-structured columns.
    return {"postgres": "JSONB", "bigquery": "JSON", "snowflake": "VARIANT"}[dialect]


def _ident(name: str, dialect: str) -> str:
    if dialect == "bigquery":
        return "`" + name.replace("`", "\\`") + "`"
    if re.fullmatch(r"[a-z_][a-z0-9_]*", name):
        return name
    return '"' + name.replace('"', '""') + '"'


def create_table(
    profile: TableProfile, table: str, dialect: str = "postgres", not_null: bool = True
) -> str:
    if dialect not in DIALECTS:
        raise ValueError(f"Unknown dialect {dialect!r}. Choose from {', '.join(DIALECTS)}.")
    defs = []
    for col in profile.columns:
        line = f"    {_ident(col.name, dialect)} {map_type(col.dtype, dialect)}"
        if not_null and col.nulls == 0 and col.non_null > 0:
            line += " NOT NULL"
        defs.append(line)
    return f"CREATE TABLE {_ident(table, dialect)} (\n" + ",\n".join(defs) + "\n);\n"
