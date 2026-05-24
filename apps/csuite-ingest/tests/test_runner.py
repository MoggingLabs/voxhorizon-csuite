"""Runner behavior: fan-out, idempotent upsert, per-connector fault isolation,
validation, and the CLI entrypoint. All in FAKE mode (no network, no creds)."""

import pytest

from src import runner
from src.base import Connector
from src.config import Settings, load_settings
from src.connectors import REGISTRY
from src.store import FakeStore

FAKE = Settings(supabase_url="", supabase_key="", fake_source=True, fake_store=True)


class _Boom(Connector):
    table = "boom"
    columns = frozenset({"id"})
    source = "boom"

    def normalize(self, raw):
        raise RuntimeError("kaboom")

    def fake_raw(self):
        return [{"id": "1"}]


def test_run_fans_out_to_every_connector():
    store = FakeStore()
    results = runner.run(FAKE, store)
    assert {r.connector for r in results} == set(REGISTRY)
    assert all(r.ok for r in results)
    assert all(r.rows > 0 for r in results)
    assert set(store.tables) == {REGISTRY[n].table for n in REGISTRY}


def test_run_selected_subset():
    store = FakeStore()
    results = runner.run(FAKE, store, names=["nps_feedback"])
    assert len(results) == 1
    assert results[0].table == "nps_feedback"
    assert store.tables["nps_feedback"]


def test_upsert_is_idempotent_on_pk():
    store = FakeStore()
    runner.run(FAKE, store, names=["nps_feedback"])
    runner.run(FAKE, store, names=["nps_feedback"])
    # two distinct fake rows, deduped by id across re-runs
    assert len(store.tables["nps_feedback"]) == 2


def test_failure_is_isolated(monkeypatch):
    monkeypatch.setattr(
        runner, "REGISTRY", {"boom": _Boom, "nps_feedback": REGISTRY["nps_feedback"]}
    )
    store = FakeStore()
    results = runner.run(FAKE, store, names=["boom", "nps_feedback"])
    by = {r.connector: r for r in results}
    assert by["boom"].ok is False and "kaboom" in by["boom"].error
    assert by["nps_feedback"].ok is True


def test_validate_rejects_unknown_column():
    c = _Boom()
    with pytest.raises(ValueError):
        runner._validate(c, [{"id": "1", "oops": 1}])


def test_validate_rejects_missing_pk():
    c = _Boom()
    with pytest.raises(ValueError):
        runner._validate(c, [{"oops": 1}])


def test_external_live_path_raises_until_wired():
    # fake_source off + external connector -> fetch() is not wired yet
    s = Settings(supabase_url="", supabase_key="", fake_source=False, fake_store=True)
    results = runner.run(s, FakeStore(), names=["nps_feedback"])
    assert results[0].ok is False


def test_main_happy(monkeypatch, capsys):
    monkeypatch.setenv("CSUITE_INGEST_FAKE_SOURCE", "1")
    monkeypatch.setenv("FAKE_STORE", "1")
    assert runner.main([]) == 0
    assert "audit_feed" in capsys.readouterr().out


def test_main_reports_failure(monkeypatch):
    monkeypatch.setenv("CSUITE_INGEST_FAKE_SOURCE", "1")
    monkeypatch.setenv("FAKE_STORE", "1")
    monkeypatch.setattr(runner, "REGISTRY", {"boom": _Boom})
    assert runner.main(["boom"]) == 1


def test_settings_defaults(monkeypatch):
    for k in (
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "CSUITE_INGEST_FAKE_SOURCE",
        "FAKE_STORE",
    ):
        monkeypatch.delenv(k, raising=False)
    s = load_settings()
    assert s.fake_source is False
    assert s.fake_store is False
    assert s.supabase_url == ""
