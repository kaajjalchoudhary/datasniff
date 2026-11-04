# datasniff check: rule cookbook

`datasniff check` exits 0 when every rule passes and 1 when any rule fails, so it drops into shell scripts, Makefiles, Airflow tasks and CI.

| Rule | Fails when |
| --- | --- |
| `--min-rows N` | the file has fewer than N rows |
| `--max-null-pct P` | any column is more than P% null |
| `--no-duplicates` | any fully duplicated row exists |
| `--unique COL` | COL has repeated values |
| `--not-null COL` | COL has any null |
| `--require-column COL` | COL is missing from the file |
| `--no-flag FLAG` | any column gets FLAG (for example `possible_pii`) |

## Common combinations

**Dimension table extract**

```bash
datasniff check customers.csv --require-column customer_id --unique customer_id --not-null customer_id
```

**Fact table extract**

```bash
datasniff check orders.parquet --min-rows 1 --no-duplicates --not-null order_id --max-null-pct 20
```

**Public release**

```bash
datasniff check release.csv --no-flag possible_pii --no-flag untrimmed_whitespace
```

**Schema drift guard**

```bash
datasniff check daily_export.csv --require-column order_id --require-column amount --require-column order_date
```

See [recipes.md](recipes.md) for full pipeline examples.
