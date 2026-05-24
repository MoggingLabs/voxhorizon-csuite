"""M8: Mission Control health-summary (per-agent latest dispatch status)."""

from fastapi.testclient import TestClient

from src.clients import FakeDispatcher
from src.config import Settings
from src.main import create_app
from src.store import FakeStore

PASS = "letmein"
SECRET = "session-secret"


def _client(store):
    settings = Settings(auth_pass=PASS, auth_secret=SECRET, dispatcher_url="http://d", dispatcher_secret="x")
    c = TestClient(create_app(settings=settings, dispatcher=FakeDispatcher(), store=store))
    c.post("/login", data={"password": PASS})
    return c


def test_health_summary_requires_auth():
    settings = Settings(auth_pass=PASS, auth_secret=SECRET, dispatcher_url="http://d", dispatcher_secret="x")
    c = TestClient(create_app(settings=settings, dispatcher=FakeDispatcher(), store=FakeStore()))
    assert c.get("/api/health-summary").status_code == 401


def test_health_summary_reports_latest_per_agent():
    # newest first; dash has a newer 'done' over an older 'error'
    store = FakeStore(dispatches=[
        {"agent": "dash", "status": "done"},
        {"agent": "dash", "status": "error"},
        {"agent": "vault", "status": "running"},
    ])
    data = _client(store).get("/api/health-summary").json()
    by_agent = {a["agent"]: a["last_status"] for a in data["agents"]}
    assert by_agent["dash"] == "done"
    assert by_agent["vault"] == "running"
    assert by_agent["rex"] is None  # no dispatches yet
    # every roster agent is represented
    assert len(data["agents"]) == 6
