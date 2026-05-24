"""Mission Control FastAPI app: the single operator interface to the C-Suite.

Auth gate (fail-closed) -> agent roster + dispatch surface + history. Dispatch
proxies to the dispatcher and streams the agent output back (SSE). No Telegram,
no Slack (ADR 0002, 0009).
"""

from __future__ import annotations

import html

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

from . import auth
from .clients import DispatcherClient, FakeDispatcher, HttpDispatcher
from .config import Settings, load_settings
from .store import FakeStore, Store, SupabaseStore


def create_app(
    settings: Settings | None = None,
    dispatcher: DispatcherClient | None = None,
    store: Store | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    if dispatcher is None:
        dispatcher = (
            FakeDispatcher()
            if settings.fake_dispatcher
            else HttpDispatcher(settings.dispatcher_url, settings.dispatcher_secret)
        )
    if store is None:
        store = FakeStore() if settings.fake_store else SupabaseStore()

    app = FastAPI(title="mission-control")

    def _authed(request: Request) -> bool:
        return auth.valid_session(request.cookies.get(auth.COOKIE), settings.auth_secret)

    def _require(request: Request) -> None:
        if not _authed(request):
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/login", response_class=HTMLResponse)
    def login_form() -> str:
        return (
            "<h1>Mission Control</h1>"
            "<form method='post' action='/login'>"
            "<input type='password' name='password' placeholder='password'>"
            "<button type='submit'>Sign in</button></form>"
        )

    @app.post("/login")
    def login(password: str = Form(default="")):
        if not auth.password_ok(password, settings.auth_pass):
            raise HTTPException(status_code=401, detail="invalid credentials")
        resp = RedirectResponse(url="/", status_code=303)
        resp.set_cookie(
            auth.COOKIE,
            auth.make_session(settings.auth_secret),
            httponly=True,
            samesite="strict",
        )
        return resp

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        if not _authed(request):
            return RedirectResponse(url="/login", status_code=303)
        rows = "".join(
            f"<li><b>{html.escape(a)}</b> - {html.escape(role)}</li>"
            for a, role in settings.roster
        )
        return (
            "<h1>Vox Horizon Mission Control</h1>"
            f"<ul>{rows}</ul>"
            f"<p>{len(settings.roster)} agents. Dispatch via POST /api/dispatch.</p>"
        )

    @app.get("/api/agents")
    def agents(request: Request):
        _require(request)
        return [{"agent": a, "role": role} for a, role in settings.roster]

    @app.get("/api/history")
    def history(request: Request):
        _require(request)
        return {
            "dispatches": store.recent_dispatches(),
            "audits": store.recent_audits(),
        }

    @app.post("/api/dispatch")
    def dispatch(body: dict, request: Request):
        _require(request)
        agent = str(body.get("agent", ""))
        prompt = str(body.get("prompt", ""))
        if agent not in {a for a, _ in settings.roster}:
            raise HTTPException(status_code=400, detail="unknown agent")
        if not prompt.strip():
            raise HTTPException(status_code=400, detail="prompt required")
        return StreamingResponse(
            dispatcher.stream(agent, prompt), media_type="text/event-stream"
        )

    app.state.settings = settings
    app.state.dispatcher = dispatcher
    app.state.store = store
    return app
