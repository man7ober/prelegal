import pytest


@pytest.fixture(autouse=True)
def isolate_database(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRELEGAL_DATABASE_PATH", str(tmp_path / "prelegal.db"))
