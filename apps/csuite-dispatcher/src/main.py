"""csuite-dispatcher FastAPI app.

Mission Control calls POST /dispatch with a bearer. The dispatcher validates the
agent against the allow-list, execs `hermes chat -q` in that container (argv, no
shell) through the scope-limited docker-socket-proxy, streams the output as SSE,
and records the dispatch + an audit row. The dispatcher never holds the raw
Docker socket (the proxy does) - controls C2, C10, C11.
"""

from __future__ import annotations

import hmac

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse

from .config import Settings, load_settings
from .executor import Executor, FakeExecutor, RealExecutor
from .store import FakeStore, SupabaseStore, Store
from .validation import resolve_container


def create_app(
    settings: Settings | None = None,
    executor: Executor | None = None,
    store: Store | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    if executor is None:
        executor = FakeExecutor() if settings.fake_docker else RealExecutor()
    if store is None:
        store = FakeStore() if settings.fake_store else SupabaseStore()

    app = FastAPI(title="csuite-dispatcher")

    def _auth(authorization: str) -> None:
        if not settings.secret:
            raise HTTPException(status_code=503, detail="dispatcher secret not configured")
        if not hmac.compare_digest(authorization or "", f"Bearer {settings.secret}"):
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/dispatch")
    def dispatch(body: dict, authorization: str = Header(default="")):
        _auth(authorization)
        agent = str(body.get("agent", ""))
        prompt = str(body.get("prompt", ""))
        try:
            container = resolve_container(agent, settings)
        except ValueError as e:
            store.audit("dispatcher", "dispatch_rejected", agent, str(e))
            raise HTTPException(status_code=400, detail=str(e))
        if not prompt.strip():
            raise HTTPException(status_code=400, detail="prompt required")

        argv = ["hermes", "chat", "-q", prompt, "--max-turns", str(settings.max_turns)]
        dispatch_id = store.start_dispatch(agent, prompt, "mission-control")
        store.audit("dispatcher", "dispatch_started", container, dispatch_id)

        def gen():
            collected: list[str] = []
            try:
                for chunk in executor.run(container, argv):
                    collected.append(chunk)
                    yield chunk
                store.finish_dispatch(dispatch_id, "done", "".join(collected)[:10000])
            except Exception as e:
                store.finish_dispatch(dispatch_id, "error", str(e))
                yield f"[error] {e}\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    app.state.settings = settings
    app.state.executor = executor
    app.state.store = store
    return app
