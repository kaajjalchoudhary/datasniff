from datasniff import profile_file
from datasniff.checks import run_checks
from datasniff.dbt import schema_yml
from datasniff.ddl import create_table, map_type


def test_dbt_schema_from_example(example_csv):
    yml = schema_yml(profile_file(example_csv), "stg_orders")
    assert "  - name: stg_orders" in yml
    order_id = yml.split("- name: order_id")[1].split("- name:")[0]
    assert "- not_null" in order_id and "- unique" not in order_id
    country = yml.split("- name: country")[1].split("- name:")[0]
    assert "values: ['AE', 'GB', 'IN', 'US']" in country
    assert "arguments:" not in yml


def test_dbt_new_syntax_and_numeric_values(write):
    rows = "\n".join(f"{i},{i % 3}" for i in range(40))
    yml = schema_yml(
        profile_file(write("t.csv", "id,bucket\n" + rows + "\n")), "m", new_syntax=True
    )
    bucket = yml.split("- name: bucket")[1]
    assert "arguments:" in bucket
    assert "values: [0, 1, 2]" in bucket and "quote: false" in bucket


def test_ddl_dialects(example_csv):
    prof = profile_file(example_csv)
    pg = create_table(prof, "orders", "postgres")
    assert "order_id BIGINT NOT NULL" in pg
    assert "amount DOUBLE PRECISION NOT NULL" in pg
    assert "discount_code TEXT\n);" in pg
    assert "order_date DATE NOT NULL" in pg

    bq = create_table(prof, "orders", "bigquery")
    assert "`order_id` INT64 NOT NULL" in bq and "`status` STRING" in bq

    sf = create_table(prof, "orders", "snowflake", not_null=False)
    assert "order_id NUMBER(38,0)," in sf and "NOT NULL" not in sf


def test_type_mapping_edge_cases():
    assert map_type("DECIMAL(18,3)", "snowflake") == "NUMBER(18,3)"
    assert map_type("TIMESTAMP WITH TIME ZONE", "bigquery") == "TIMESTAMP"
    assert map_type("STRUCT(a INTEGER)", "postgres") == "JSONB"
    assert map_type("VARCHAR", "duckdb") == "VARCHAR"


def test_checks(example_csv):
    prof = profile_file(example_csv)
    results = {
        r.rule: r.passed
        for r in run_checks(
            prof,
            min_rows=10,
            no_duplicates=True,
            unique=["order_id"],
            not_null=["order_id", "discount_code"],
            require_columns=["amount", "missing_col"],
            max_null_pct=80,
        )
    }
    assert results == {
        "column exists: amount": True,
        "column exists: missing_col": False,
        "rows >= 10": True,
        "no duplicate rows": False,
        "null % <= 80 in every column": True,
        "unique: order_id": False,
        "not null: order_id": True,
        "not null: discount_code": False,
    }
