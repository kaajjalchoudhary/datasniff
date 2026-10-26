# Changelog

All notable changes to datasniff are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-10-25

### Added
- `datasniff profile`: per-column type, null %, distinct count, min/max, top values and data quality
  flags, as text, Markdown or JSON.
- `datasniff dbt`: generates a dbt `schema.yml` with `not_null`, `unique` and `accepted_values` tests.
- `datasniff ddl`: `CREATE TABLE` for Postgres, BigQuery, Snowflake and DuckDB.
- `datasniff check`: pass/fail rules with a non-zero exit code for CI.
- Reusable GitHub Action that adds the profile to the job summary.

### Fixed
- Generated `accepted_values` are trimmed, so values with stray whitespace fail the test instead of
  being accepted by it.
