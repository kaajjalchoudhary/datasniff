"""Command-line interface.

datasniff orders.csv                         # profile (default command)
datasniff profile data/*.parquet --format markdown -o PROFILE.md
datasniff dbt orders.csv --model stg_orders -o models/staging/stg_orders.yml
datasniff ddl orders.csv --dialect bigquery --table analytics.orders
datasniff check orders.csv --unique order_id --no-duplicates --max-null-pct 5
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from datasniff import __version__
from datasniff.checks import run_checks
from datasniff.dbt import schema_yml
from datasniff.ddl import DIALECTS, create_table
from datasniff.profile import profile_file
from datasniff.reader import UnsupportedFormat
from datasniff.render import summary_line, to_json, to_markdown, to_text

COMMANDS = {"profile", "dbt", "ddl", "check"}


def _default_name(path: str) -> str:
    stem = Path(path.split("*")[0].rstrip("/") or "data").name.split(".")[0] or "data"
    return re.sub(r"[^0-9a-zA-Z_]+", "_", stem).strip("_").lower() or "data"


def _emit(text: str, output: str | None) -> None:
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
        print(f"wrote {output}", file=sys.stderr)
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="datasniff",
        description="Profile, validate and generate dbt tests / DDL for CSV, Parquet and JSON.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("profile", help="profile a file (default command)")
    pr.add_argument("path")
    pr.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    pr.add_argument("--top", type=int, default=3, help="top values to show per column")
    pr.add_argument("-o", "--output")

    db = sub.add_parser("dbt", help="generate a dbt schema.yml with inferred tests")
    db.add_argument("path")
    db.add_argument("--model", help="model name (default: file name)")
    db.add_argument(
        "--new-test-syntax",
        action="store_true",
        help="nest test arguments under `arguments:` (dbt >= 1.10)",
    )
    db.add_argument("-o", "--output")

    dd = sub.add_parser("ddl", help="generate a CREATE TABLE statement")
    dd.add_argument("path")
    dd.add_argument("--dialect", choices=DIALECTS, default="postgres")
    dd.add_argument("--table", help="table name (default: file name)")
    dd.add_argument("--no-not-null", action="store_true", help="never emit NOT NULL")
    dd.add_argument("-o", "--output")

    ck = sub.add_parser("check", help="validate a file; exits 1 if any rule fails")
    ck.add_argument("path")
    ck.add_argument("--min-rows", type=int)
    ck.add_argument("--max-null-pct", type=float)
    ck.add_argument("--no-duplicates", action="store_true")
    ck.add_argument("--unique", action="append", default=[], metavar="COLUMN")
    ck.add_argument("--not-null", action="append", default=[], metavar="COLUMN")
    ck.add_argument("--require-column", action="append", default=[], metavar="COLUMN")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        argv.insert(0, "profile")
    args = build_parser().parse_args(argv)

    try:
        top = getattr(args, "top", 3)
        profile = profile_file(args.path, top_n=top)
    except UnsupportedFormat as exc:
        print(f"datasniff: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # surface DuckDB read errors without a traceback
        print(f"datasniff: could not read {args.path!r}: {exc}", file=sys.stderr)
        return 2

    if args.command == "profile":
        render = {"text": to_text, "markdown": to_markdown, "json": to_json}[args.format]
        _emit(render(profile), args.output)
    elif args.command == "dbt":
        _emit(
            schema_yml(profile, args.model or _default_name(args.path), args.new_test_syntax),
            args.output,
        )
    elif args.command == "ddl":
        table = args.table or _default_name(args.path)
        _emit(create_table(profile, table, args.dialect, not args.no_not_null), args.output)
    elif args.command == "check":
        results = run_checks(
            profile,
            min_rows=args.min_rows,
            max_null_pct=args.max_null_pct,
            no_duplicates=args.no_duplicates,
            unique=args.unique,
            not_null=args.not_null,
            require_columns=args.require_column,
        )
        if not results:
            print("datasniff: no rules given (see `datasniff check --help`)", file=sys.stderr)
            return 2
        print(summary_line(profile))
        for r in results:
            print(f"  {'PASS' if r.passed else 'FAIL'}  {r.rule}  ({r.details})")
        failed = sum(not r.passed for r in results)
        print(f"{len(results) - failed}/{len(results)} checks passed")
        return 1 if failed else 0
    return 0
