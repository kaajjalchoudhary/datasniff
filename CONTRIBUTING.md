# Contributing to datasniff

Thanks for helping make datasniff better! Bug reports, ideas, docs fixes and code are all welcome.

## Ways to help

- **Report a bug**: open an issue with the file type, the command you ran, what you expected and
  what happened. A tiny sample file (no real personal data, please) helps a lot.
- **Suggest a check or output format**: open a feature request and describe the data problem it
  would catch.
- **Improve the docs**: typos, clearer examples and missing flags in the README are great first PRs.
- **Write code**: look for issues labelled `good first issue` or `help wanted`.

## Development setup

You need Python 3.9 or newer.

```bash
git clone https://github.com/kaajjalchoudhary/datasniff.git
cd datasniff
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Check everything works:

```bash
pytest -v
ruff check .
datasniff examples/orders.csv
```

## Project layout

| Path | What lives there |
|---|---|
| `src/datasniff/reader.py` | Detects the file format and builds the DuckDB `read_*` source |
| `src/datasniff/profile.py` | Column profiling and data quality flags |
| `src/datasniff/checks.py` | Pass/fail rules used by `datasniff check` |
| `src/datasniff/dbt.py` | dbt `schema.yml` generation |
| `src/datasniff/ddl.py` | `CREATE TABLE` generation per SQL dialect |
| `src/datasniff/render.py` | Text, Markdown and JSON output |
| `src/datasniff/cli.py` | Command-line interface |
| `tests/` | pytest suite (`write` fixture creates small test files) |
| `examples/orders.csv` | Sample data used by the tests, CI and README |
| `action.yml` | The reusable GitHub Action |

## Adding a new data quality flag

1. Add the logic in `_flags()` in `src/datasniff/profile.py`.
2. Add a test in `tests/test_profile.py`, using the `write` fixture to build a small file that
   triggers the flag (and ideally one that doesn't).
3. Add the flag to the **Flags reference** table in `README.md`.
4. Add a line under `## [Unreleased]` in `CHANGELOG.md`.

## Adding a new check rule

1. Add a keyword argument and a `CheckResult` in `run_checks()` in `src/datasniff/checks.py`.
2. Wire up the CLI option in `src/datasniff/cli.py`.
3. Test both the passing and the failing case.
4. Document it in the README and `CHANGELOG.md`.

## Pull request checklist

- [ ] `pytest` passes
- [ ] `ruff check .` passes (line length is 100)
- [ ] New behaviour has tests
- [ ] README and `CHANGELOG.md` are updated if users will notice the change
- [ ] One focused change per PR

CI runs the tests on Linux, macOS and Windows, smoke-tests every CLI command and runs the GitHub
Action against `examples/orders.csv`, so a green check means it works everywhere.

## Commit messages

Use short, imperative messages that say what changed, for example
`Add outlier flag for numeric columns` or `Fix BigQuery DDL for nested JSON`.

## Code of conduct

Be kind and assume good intent. Harassment or personal attacks aren't welcome here.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
