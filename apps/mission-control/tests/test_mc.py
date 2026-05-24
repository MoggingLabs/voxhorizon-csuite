"""Mission Control tests (auth gate, roster, dispatch proxy, history).

All run with FakeDispatcher + FakeStore, so CI needs no dispatcher or DB.
"""

from fastapi.testclient import TestClient

from src import auth
from src.clients import FakeDispatcher
from src.config import Settings
from src.main import create_app
from src.store import FakeStore

PASS = "letmein"
SECRET = "session-secret"


def _settings(**kw):
    base = dict(auth_pass=PASS, auth_secret=SECRET, dispatcher_url="http://d", dispatcher_secret="x")
    base.update(kw)
    return Settings(**base)


def _client(dispatcher=None, store=None, settings=None, follow=True):
    app = create_app(
        settings=settings or _settings(),
        dispatcher=dispatcher or FakeDispatcher(),
        store=store or FakeStore(),
    )
    return TestClient(app, follow_redirects=follow)


def _login(c):
    assert c.post("/login", data={"password": PASS}).status_code in (200, 303)
    return c


def test_health():
    assert _client().get("/health").json()["status"] == "ok"


def test_home_redirects_when_unauthed():
    c = _client(follow=False)
    r = c.get("/")
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_login_form_renders():
    r = _client().get("/login")
    assert r.status_code == 200 and "password" in r.text


def test_login_wrong_password_rejected():
    assert _client().post("/login", data={"password": "nope"}).status_code == 401


def test_login_then_home_shows_roster():
    r = _login(_client()).get("/")
    assert r.status_code == 200
    assert "rex" in r.text and "pulse" in r.text


def test_api_agents_requires_auth():
    assert _client().get("/api/agents").status_code == 401


def test_api_agents_when_authed():
    data = _login(_client()).get("/api/agents").json()
    assert {a["agent"] for a in data} == {"rex", "dash", "closer", "vault", "bob", "pulse"}


def test_dispatch_streams():
    ex = FakeDispatcher()
    r = _login(_client(dispatcher=ex)).post("/api/dispatch", json={"agent": "dash", "prompt": "hi"})
    assert r.status_code == 200
    assert "dispatched dash" in r.text
    assert ex.calls == [("dash", "hi")]


def test_dispatch_unknown_agent_rejected():
    assert _login(_client()).post("/api/dispatch", json={"agent": "ops", "prompt": "x"}).status_code == 400


def test_dispatch_empty_prompt_rejected():
    assert _login(_client()).post("/api/dispatch", json={"agent": "rex", "prompt": " "}).status_code == 400


def test_dispatch_requires_auth():
    assert _client().post("/api/dispatch", json={"agent": "rex", "prompt": "x"}).status_code == 401


def test_history_when_authed():
    store = FakeStore(dispatches=[{"agent": "rex", "status": "done"}], audits=[{"action": "dispatch_started"}])
    data = _login(_client(store=store)).get("/api/history").json()
    assert data["dispatches"][0]["agent"] == "rex"
    assert data["audits"][0]["action"] == "dispatch_started"


def test_auth_helpers():
    s = auth.make_session(SECRET)
    assert auth.valid_session(s, SECRET)
    assert not auth.valid_session(s, "other-secret")
    assert not auth.valid_session(s, "")
    assert not auth.valid_session("malformed", SECRET)
    assert not auth.valid_session(None, SECRET)
    assert auth.password_ok(PASS, PASS)
    assert not auth.password_ok("x", PASS)
    assert not auth.password_ok(PASS, "")


def test_default_selection_uses_fakes(monkeypatch):
    monkeypatch.setenv("MC_AUTH_PASS", PASS)
    monkeypatch.setenv("MC_AUTH_SECRET", SECRET)
    monkeypatch.setenv("FAKE_DISPATCHER", "true")
    monkeypatch.setenv("FAKE_STORE", "true")
    c = TestClient(create_app())
    assert c.get("/health").status_code == 200
    c.post("/login", data={"password": PASS})
    assert c.get("/api/agents").status_code == 200
