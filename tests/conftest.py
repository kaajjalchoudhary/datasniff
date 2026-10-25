from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def example_csv() -> str:
    return str(ROOT / "examples" / "orders.csv")


@pytest.fixture
def write(tmp_path):
    def _write(name: str, text: str) -> str:
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    return _write
