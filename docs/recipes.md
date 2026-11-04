# Recipes

Copy-paste workflows built from the four datasniff commands. Every flag used here is documented in the main README.

## 1. Bootstrap a dbt staging model from a new source file

```bash
# Look first
datasniff raw/orders.csv

# Generate tests for the staging model
datasniff dbt raw/orders.csv --model stg_orders -o models/staging/stg_orders.yml

# On dbt >= 1.10 use the new test syntax
datasniff dbt raw/orders.csv --model stg_orders --new-test-syntax -o models/staging/stg_orders.yml
```

Review the generated `accepted_values` lists before committing: they describe the data you have today, not the business rules.

## 2. Create the landing table in your warehouse

```bash
datasniff ddl raw/orders.csv --dialect snowflake --table raw.orders > ddl/raw_orders.sql
datasniff ddl raw/orders.csv --dialect postgres  --table raw.orders > ddl/raw_orders_pg.sql
```

Columns with no nulls in the sample get `NOT NULL`. If later loads may be sparser, relax those constraints by hand.

## 3. Gate a load in a shell pipeline

```bash
set -e
datasniff check exports/customers.csv \
  --min-rows 1 \
  --unique customer_id \
  --no-duplicates \
  --max-null-pct 10
# Only reached when every rule passed (exit code 0)
./load_customers.sh
```

## 4. Profile a whole folder of Parquet exports at once

```bash
datasniff profile 'exports/*.parquet' --format markdown -o PROFILE.md
```

Quote the glob so DuckDB, not your shell, expands it.

## 5. Block PII from landing in a public dataset

```bash
datasniff check public/release.csv --no-flag possible_pii
```

## 6. Keep a profile snapshot in version control

```bash
datasniff profile data/products.parquet --format json -o profiles/products.json
git diff profiles/products.json   # see how the data shifted since last time
```

## 7. Use it from Python in a notebook or Airflow task

```python
from datasniff import profile_file

p = profile_file("exports/orders.parquet")
if p.duplicate_rows:
    raise ValueError(f"{p.duplicate_rows} duplicate rows in orders export")
```
