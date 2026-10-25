from datasniff.cli import _default_name, main


def test_profile_is_the_default_command(example_csv, capsys):
    assert main([example_csv]) == 0
    out = capsys.readouterr().out
    assert "61 rows · 8 columns · 1 duplicate row" in out
    assert "possible_pii" in out


def test_markdown_and_json(example_csv, capsys):
    assert main(["profile", example_csv, "--format", "markdown"]) == 0
    assert "| `order_id` | `BIGINT` |" in capsys.readouterr().out
    assert main(["profile", example_csv, "--format", "json"]) == 0
    assert '"duplicate_rows": 1' in capsys.readouterr().out


def test_check_exit_codes(example_csv, capsys):
    assert main(["check", example_csv, "--not-null", "order_id", "--min-rows", "10"]) == 0
    assert main(["check", example_csv, "--no-duplicates"]) == 1
    assert "FAIL  no duplicate rows" in capsys.readouterr().out
    assert main(["check", example_csv]) == 2  # no rules given


def test_writes_output_files(example_csv, tmp_path):
    out = tmp_path / "models" / "stg_orders.yml"
    assert main(["dbt", example_csv, "-o", str(out)]) == 0
    assert "name: orders" in out.read_text()
    sql = tmp_path / "orders.sql"
    assert (
        main(["ddl", example_csv, "--dialect", "bigquery", "--table", "raw.orders", "-o", str(sql)])
        == 0
    )
    assert sql.read_text().startswith("CREATE TABLE `raw.orders`")


def test_bad_inputs(capsys, tmp_path):
    assert main(["report.xlsx"]) == 2
    assert main([str(tmp_path / "missing.csv")]) == 2
    assert "could not read" in capsys.readouterr().err


def test_default_name():
    assert _default_name("data/Raw Orders-2024.csv") == "raw_orders_2024"
    assert _default_name("lake/events/*.parquet") == "events"
