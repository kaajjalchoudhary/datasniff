"""Assertions for gating pipelines / CI on a data file."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from datasniff.profile import TableProfile


@dataclass
class CheckResult:
    rule: str
    passed: bool
    details: str


def run_checks(
    profile: TableProfile,
    *,
    min_rows: int | None = None,
    max_null_pct: float | None = None,
    no_duplicates: bool = False,
    unique: Iterable[str] = (),
    not_null: Iterable[str] = (),
    require_columns: Iterable[str] = (),
) -> list[CheckResult]:
    results: list[CheckResult] = []
    names = {c.name for c in profile.columns}

    for col in require_columns:
        results.append(
            CheckResult(
                f"column exists: {col}", col in names, "missing" if col not in names else "ok"
            )
        )
    if min_rows is not None:
        results.append(
            CheckResult(f"rows >= {min_rows}", profile.rows >= min_rows, f"{profile.rows:,} rows")
        )
    if no_duplicates:
        d = profile.duplicate_rows
        results.append(CheckResult("no duplicate rows", d == 0, f"{d:,} duplicate rows"))
    if max_null_pct is not None:
        worst = [c for c in profile.columns if c.null_pct > max_null_pct]
        details = ", ".join(f"{c.name} {c.null_pct:g}%" for c in worst) or "ok"
        results.append(
            CheckResult(f"null % <= {max_null_pct:g} in every column", not worst, details)
        )
    for name in unique:
        if name not in names:
            results.append(CheckResult(f"unique: {name}", False, "column missing"))
            continue
        c = profile.column(name)
        ok = c.nulls == 0 and c.distinct == profile.rows
        results.append(
            CheckResult(
                f"unique: {name}",
                ok,
                f"{c.distinct:,} distinct / {profile.rows:,} rows, {c.nulls:,} nulls",
            )
        )
    for name in not_null:
        if name not in names:
            results.append(CheckResult(f"not null: {name}", False, "column missing"))
            continue
        c = profile.column(name)
        results.append(CheckResult(f"not null: {name}", c.nulls == 0, f"{c.nulls:,} nulls"))
    return results
