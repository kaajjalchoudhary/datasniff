import duckdb
import pytest

from datasniff import profile_file
from datasniff.reader import UnsupportedFormat, source_sql


def test_example_file_profile(example_csv):
    prof = profile_file(example_csv)
    assert prof.rows == 61
    assert prof.duplicate_rows == 1
    assert prof.column("order_id").dtype == "BIGINT"
    assert "unique" not in prof.column("order_id").flags  # the duplicate row repeats an id
    assert "constant" in prof.column("currency").flags
    assert "high_nulls" in prof.column("discount_code").flags
    assert "possible_pii" in prof.column("customer_email").flags
    assert "categorical" in prof.column("country").flags
    assert prof.column("country").all_values == ["AE", "GB", "IN", "US"]


def test_unique_and_numeric_stats(write):
    rows = "\n".join(f"{i},{i * 10}" for i in range(1, 31))
    prof = profile_file(write("t.csv", "id,score\n" + rows + "\n"))
    ident = prof.column("id")
    assert ident.flags == ["unique"]
    assert (ident.min, ident.max) == ("1", "30")
    assert prof.column("score").mean == 155.0


def test_json_flags_whitespace_and_numeric_text(write):
    lines = [f'{{"code": " {i % 3}", "qty": "{i}", "meta": {{"a": {i}}}}}' for i in range(25)]
    prof = profile_file(write("t.ndjson", "\n".join(lines) + "\n"))
    assert "untrimmed_whitespace" in prof.column("code").flags
    assert "numeric_as_text" in prof.column("qty").flags
    assert prof.column("meta").min is None  # nested types are profiled without min/max


def test_parquet_and_null_handling(tmp_path):
    path = tmp_path / "t.parquet"
    with duckdb.connect() as con:
        con.execute(
            f"COPY (SELECT i AS id, CASE WHEN i % 2 = 0 THEN NULL ELSE 'x' END AS half_null, "
            f"NULL::VARCHAR AS empty FROM range(10) t(i)) TO '{path}' (FORMAT parquet)"
        )
    prof = profile_file(str(path))
    assert prof.column("half_null").null_pct == 50.0
    assert "high_nulls" in prof.column("half_null").flags
    assert "all_null" in prof.column("empty").flags


def test_unsupported_format():
    with pytest.raises(UnsupportedFormat):
        source_sql("report.xlsx")


def test_paths_with_quotes_are_escaped():
    assert source_sql("it's.csv").startswith("read_csv_auto('it''s.csv'")
