# FAQ

### Does datasniff load the whole file into memory?

No. It queries files through DuckDB, which streams CSV, Parquet and JSON, so multi-GB files and globs work without pandas.

### Which file formats are supported?

CSV, Parquet and JSON, plus glob patterns such as `'exports/*.parquet'`.

### Why does a column show more distinct values than I expected?

Usually dirty values. The `untrimmed_whitespace` flag catches values like `" shipped"`, which count as different from `"shipped"`. See the example in the README.

### The generated `accepted_values` test fails on my data. Is that a bug?

Often it is the point. Accepted values are trimmed, so rows with stray spaces fail the test instead of being silently accepted.

### Is `possible_pii` reliable?

It is a heuristic based on column names and value patterns (emails, phones, SSN, dates of birth, addresses). Treat it as a prompt to look, not as proof either way.

### Which dbt version do the tests target?

The default output works with current dbt versions. Pass `--new-test-syntax` for dbt 1.10 and later.

### How do I fail CI when data is bad?

Use `datasniff check` with one or more rules. It exits with code 1 when any rule fails, or use the bundled GitHub Action (see the README).

### Does it send my data anywhere?

No. Everything runs locally; the only dependency is `duckdb`.
