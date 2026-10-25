"""Column-level profiling powered by DuckDB (fast, out-of-core, no pandas needed)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

import duckdb

from datasniff.reader import source_sql

VIEW = "__datasniff_src"
ACCEPTED_VALUES_MAX = 10

NUMERIC_TYPES = (
    "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT",
    "UINTEGER", "UBIGINT", "UHUGEINT", "FLOAT", "DOUBLE", "REAL", "DECIMAL",
)  # fmt: skip
NESTED_MARKERS = ("[", "STRUCT", "MAP", "UNION")
PII_NAME = re.compile(
    r"(e-?mail|phone|mobile|ssn|social_security|passport|birth|dob|address|ip_?addr|iban|"
    r"card_?number|credit_?card|national_id|tax_id)",
    re.IGNORECASE,
)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    non_null: int
    nulls: int
    null_pct: float
    distinct: int
    min: str | None
    max: str | None
    mean: float | None
    top_values: list[tuple[str, int]] = field(default_factory=list)
    all_values: list[str] | None = None  # every distinct value, when there are only a few
    flags: list[str] = field(default_factory=list)

    @property
    def is_numeric(self) -> bool:
        return self.dtype.upper().startswith(NUMERIC_TYPES)

    @property
    def is_text(self) -> bool:
        return self.dtype.upper() == "VARCHAR"


@dataclass
class TableProfile:
    source: str
    rows: int
    duplicate_rows: int
    columns: list[ColumnProfile]

    def column(self, name: str) -> ColumnProfile:
        for col in self.columns:
            if col.name == name:
                return col
        raise KeyError(f"No column named {name!r}. Columns: {[c.name for c in self.columns]}")

    def to_dict(self) -> dict:
        return asdict(self)


def _flags(col: ColumnProfile, rows: int, untrimmed: int, numeric_like: int) -> list[str]:
    flags = []
    if rows and col.non_null == 0:
        flags.append("all_null")
    elif col.null_pct >= 50:
        flags.append("high_nulls")
    if col.distinct == 1:
        flags.append("constant")
    if rows and col.nulls == 0 and col.distinct == rows:
        flags.append("unique")
    elif rows >= 20 and 1 < col.distinct <= min(20, rows // 4):
        flags.append("categorical")
    if untrimmed:
        flags.append("untrimmed_whitespace")
    if col.is_text and col.non_null and numeric_like == col.non_null:
        flags.append("numeric_as_text")
    looks_like_email = col.is_text and any(EMAIL.match(v.strip()) for v, _ in col.top_values)
    if PII_NAME.search(col.name) or looks_like_email:
        flags.append("possible_pii")
    return flags


def _profile_column(
    con: duckdb.DuckDBPyConnection, name: str, dtype: str, rows: int, top_n: int
) -> ColumnProfile:
    c = quote_ident(name)
    upper = dtype.upper()
    nested = any(m in upper for m in NESTED_MARKERS)
    is_num = upper.startswith(NUMERIC_TYPES)
    is_text = upper == "VARCHAR"

    exprs = [
        f"count({c})",
        f"count(DISTINCT {c})",
        "NULL" if nested else f"CAST(min({c}) AS VARCHAR)",
        "NULL" if nested else f"CAST(max({c}) AS VARCHAR)",
        f"avg({c})" if is_num else "NULL",
        f"count(*) FILTER (WHERE {c} <> trim({c}))" if is_text else "0",
        f"count(TRY_CAST({c} AS DOUBLE))" if is_text else "0",
    ]
    non_null, distinct, mn, mx, mean, untrimmed, numeric_like = con.execute(
        f"SELECT {', '.join(exprs)} FROM {VIEW}"
    ).fetchone()

    limit = max(top_n, ACCEPTED_VALUES_MAX)
    values = con.execute(
        f"SELECT CAST({c} AS VARCHAR) AS v, count(*) AS n FROM {VIEW} "
        f"WHERE {c} IS NOT NULL GROUP BY 1 ORDER BY n DESC, v LIMIT {limit}"
    ).fetchall()

    nulls = rows - non_null
    col = ColumnProfile(
        name=name,
        dtype=dtype,
        non_null=non_null,
        nulls=nulls,
        null_pct=round(100.0 * nulls / rows, 2) if rows else 0.0,
        distinct=distinct,
        min=mn,
        max=mx,
        mean=round(float(mean), 4) if mean is not None else None,
        top_values=[(v, n) for v, n in values[:top_n]],
        all_values=sorted(v for v, _ in values) if distinct <= ACCEPTED_VALUES_MAX else None,
    )
    col.flags = _flags(col, rows, untrimmed, numeric_like)
    return col


def profile_file(
    path: str, top_n: int = 3, con: duckdb.DuckDBPyConnection | None = None
) -> TableProfile:
    """Profile a CSV / Parquet / JSON file (or glob) and return a :class:`TableProfile`."""
    own = con is None
    con = con or duckdb.connect()
    try:
        con.execute(f"CREATE OR REPLACE TEMP VIEW {VIEW} AS SELECT * FROM {source_sql(path)}")
        schema = con.execute(f"DESCRIBE {VIEW}").fetchall()
        rows = con.execute(f"SELECT count(*) FROM {VIEW}").fetchone()[0]
        distinct_rows = con.execute(
            f"SELECT count(*) FROM (SELECT DISTINCT * FROM {VIEW})"
        ).fetchone()[0]
        columns = [_profile_column(con, r[0], r[1], rows, top_n) for r in schema]
    finally:
        if own:
            con.close()
    return TableProfile(
        source=path, rows=rows, duplicate_rows=rows - distinct_rows, columns=columns
    )
