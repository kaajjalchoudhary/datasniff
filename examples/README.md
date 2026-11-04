# Examples

## `orders.csv`

A small, deliberately messy orders export (61 rows, 8 columns) used in the README and in CI. It contains one problem of each kind datasniff is built to catch:

| Problem | Where | Flag / finding |
| --- | --- | --- |
| Double-loaded row | `order_id` 1020 appears twice | duplicate row |
| Stray whitespace | `status` has `" shipped"` | `untrimmed_whitespace` |
| Column with one value | `currency` is always `USD` | `constant` |
| Mostly empty column | `discount_code` is ~77% null | `high_nulls` |
| Personal data | `customer_email` | `possible_pii` |

Try it:

```bash
datasniff examples/orders.csv
datasniff dbt examples/orders.csv --model stg_orders
datasniff ddl examples/orders.csv --dialect duckdb --table raw.orders
datasniff check examples/orders.csv --no-duplicates   # exits 1
```

Please keep this file byte-for-byte stable: tests and the README output depend on it.
