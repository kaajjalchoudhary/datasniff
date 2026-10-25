# datasniff 🔍

[![CI](https://github.com/kaajjalchoudhary/datasniff/actions/workflows/ci.yml/badge.svg)](https://github.com/kaajjalchoudhary/datasniff/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Powered by DuckDB](https://img.shields.io/badge/powered%20by-DuckDB-FFF000?logo=duckdb&logoColor=black)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Know your data file before you load it.** One command profiles any CSV, Parquet or JSON file, flags
data quality problems, and writes the boilerplate you were going to write by hand: a **dbt
`schema.yml` with tests** and a **`CREATE TABLE`** for Postgres, BigQuery, Snowflake or DuckDB.

- ⚡ **Fast on big files.** Built on DuckDB, so it streams multi-GB files and globs like
  `exports/*.parquet` without pandas.
- 🔎 **Finds problems for you**: duplicate rows, high-null and all-null columns, constant columns,
  untrimmed whitespace, numbers stored as text, likely PII (emails, phones…), candidate keys and
  low-cardinality columns.
- 🧪 **Generates dbt tests** (`not_null`, `unique`, `accepted_values`) from what the data actually looks like.
- 🏗️ **Generates DDL** with the right types per warehouse.
- 🚦 **Gates pipelines**: `datasniff check` exits non-zero when a rule fails, and it ships as a
  GitHub Action.
- 🪶 **One dependency** (`duckdb`).

## Install

```bash
pip install git+https://github.com/kaajjalchoudhary/datasniff.git
```

## Usage

```bash
datasniff orders.csv                                    # profile (default command)
datasniff profile 'exports/*.parquet' --format markdown -o PROFILE.md
datasniff dbt orders.csv --model stg_orders -o models/staging/stg_orders.yml
datasniff ddl orders.csv --dialect bigquery --table raw.orders
datasniff check orders.csv --unique order_id --no-duplicates --max-null-pct 5
```

Try it on the bundled messy sample: `datasniff examples/orders.csv`.

| Command | What you get |
|---|---|
| `profile` | Row count, duplicates, and per column: type, null %, distinct count, min/max, top values, flags. Output as `text`, `markdown` (paste into a PR or wiki) or `json` |
| `dbt` | `schema.yml` with `not_null`, `unique` and `accepted_values` tests inferred from the data. Use `--new-test-syntax` for dbt ≥ 1.10 |
| `ddl` | `CREATE TABLE` for `postgres`, `bigquery`, `snowflake` or `duckdb`, with `NOT NULL` where the data has no nulls |
| `check` | Pass/fail rules (`--min-rows`, `--max-null-pct`, `--no-duplicates`, `--unique COL`, `--not-null COL`, `--require-column COL`). Exit code 1 on failure |

## Use it in GitHub Actions

Validate data files on every pull request, with the profile added to the job summary:

```yaml
- uses: kaajjalchoudhary/datasniff@main
  with:
    path: data/customers.csv
    args: --unique customer_id --no-duplicates --max-null-pct 10
```

## Use it from Python

```python
from datasniff import profile_file

profile = profile_file("orders.parquet")
print(profile.rows, profile.duplicate_rows)
for col in profile.columns:
    print(col.name, col.dtype, col.null_pct, col.flags)
```

## Flags reference

| Flag | Meaning |
|---|---|
| `unique` | No nulls and every value distinct (candidate key) |
| `categorical` | Few distinct values compared to rows (good `accepted_values` candidate) |
| `constant` | Only one distinct value |
| `high_nulls` / `all_null` | 50%+ / 100% nulls |
| `untrimmed_whitespace` | Text values with leading or trailing spaces |
| `numeric_as_text` | Text column where every value parses as a number |
| `possible_pii` | Column name or values look like personal data (email, phone, SSN, DOB, address…) |

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

CI runs the test suite on Linux, macOS and Windows (Python 3.9 and 3.12), smoke-tests every CLI
command, and runs this repo's own GitHub Action against the sample data.

## License

MIT
