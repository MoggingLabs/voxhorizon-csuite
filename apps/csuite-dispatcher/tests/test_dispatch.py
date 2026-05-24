"""Dispatcher tests, including the C2/C11 abuse cases.

All run with FAKE_DOCKER/FAKE_STORE doubles, so CI needs no Docker daemon or
Supabase. Coverage gate is 90 percent.
"""

from typing import Iterator, List

import pytest
from fastapi.testclient import TestClient

from src.config import Settings
from src.executor import FakeExecutor
from src.main import create_app
from src.store import FakeStore

SECRET = "test-secret-not-real"
AUTH = {"Authorization": f"Bearer {SECRET}"}


def _settings(**kw):
    base = dict(
        secret=SECRET,
        allowlist=frozenset({"rex", "dash", "closer", "vault", "bob", "pulse"}),
    )
    base.update(kw)
    return Settings(**base)


def _client(executor=None, store=None, settings=None):
    settings = settings or _settings()
    executor = executor or FakeExecutor()
    store = store or FakeStore()
    app = create_app(settings=settings, executor=executor, store=store)
    return TestClient(app), executor, store


def test_health_ok():
    c, _, _ = _client()
    assert c.get("/health").json() == {"status": "ok"}


def test_dispatch_happy_path_streams_and_records():
    c, ex, store = _client()
    r = c.post("/dispatch", json={"agent": "dash", "prompt": "daily brief"}, headers=AUTH)
    assert r.status_code == 200
    assert "[fake] exec in csuite-hermes-dash" in r.text
    # exec used an argv array, never a shell string
    assert ex.calls[0][0] == "csuite-hermes-dash"
    assert ex.calls[0][1][:4] == ["hermes", "chat", "-q", "daily brief"]
    # one dispatch recorded + finished, plus an audit row
    (did, row) = next(iter(store.dispatches.items()))
    assert row["status"] == "done"
    assert any(a["action"] == "dispatch_started" for a in store.audits)


def test_missing_bearer_rejected():
    c, _, _ = _client()
    r = c.post("/dispatch", json={"agent": "dash", "prompt": "x"})
    assert r.status_code == 401


def test_wrong_bearer_rejected():
    c, _, _ = _client()
    r = c.post("/dispatch", json={"agent": "dash", "prompt": "x"}, headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


def test_secret_unconfigured_fails_closed():
    c, _, _ = _client(settings=_settings(secret=""))
    r = c.post("/dispatch", json={"agent": "dash", "prompt": "x"}, headers=AUTH)
    assert r.status_code == 503


def test_foreign_container_rejected_and_audited():
    c, ex, store = _client()
    r = c.post("/dispatch", json={"agent": "voxhorizon-web", "prompt": "x"}, headers=AUTH)
    assert r.status_code == 400
    assert ex.calls == []  # never executed
    assert any(a["action"] == "dispatch_rejected" for a in store.audits)


def test_not_allowlisted_agent_rejected():
    c, ex, _ = _client()
    r = c.post("/dispatch", json={"agent": "ops", "prompt": "x"}, headers=AUTH)
    assert r.status_code == 400
    assert ex.calls == []


def test_shell_injection_in_name_rejected():
    c, ex, _ = _client()
    for bad in ("rex; rm -rf /", "rex && id", "../etc", "rex`whoami`"):
        r = c.post("/dispatch", json={"agent": bad, "prompt": "x"}, headers=AUTH)
        assert r.status_code == 400
    assert ex.calls == []


def test_empty_prompt_rejected():
    c, _, _ = _client()
    r = c.post("/dispatch", json={"agent": "dash", "prompt": "   "}, headers=AUTH)
    assert r.status_code == 400


def test_executor_error_recorded():
    class Raiser:
        def run(self, container: str, argv: List[str]) -> Iterator[str]:
            raise RuntimeError("boom")
            yield  # pragma: no cover

    c, _, store = _client(executor=Raiser())
    r = c.post("/dispatch", json={"agent": "rex", "prompt": "go"}, headers=AUTH)
    assert "[error] boom" in r.text
    (did, row) = next(iter(store.dispatches.items()))
    assert row["status"] == "error"


def test_default_selection_uses_fakes(monkeypatch):
    monkeypatch.setenv("CSUITE_DISPATCHER_SECRET", SECRET)
    monkeypatch.setenv("FAKE_DOCKER", "true")
    monkeypatch.setenv("FAKE_STORE", "true")
    app = create_app()  # no injection: picks FakeExecutor + FakeStore
    c = TestClient(app)
    assert c.get("/health").status_code == 200
    r = c.post("/dispatch", json={"agent": "bob", "prompt": "hi"}, headers=AUTH)
    assert r.status_code == 200
