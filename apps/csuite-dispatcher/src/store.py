"""Persistence for dispatches and the audit log (control C10).

FakeStore is an in-memory double for CI (FAKE_STORE). SupabaseStore writes to the
self-hosted Supabase via PostgREST with the service role (server-side only).
"""

from __future__ import annotations

import os
import uuid
from typing import Protocol


class Store(Protocol):
    def start_dispatch(self, agent: str, prompt: str, requested_by: str) -> str: ...
    def finish_dispatch(self, dispatch_id: str, status: str, result: str) -> None: ...
    def audit(self, actor: str, action: str, target: str, detail: str) -> None: ...


class FakeStore:
    def __init__(self) -> None:
        self.dispatches: dict[str, dict] = {}
        self.audits: list[dict] = []

    def start_dispatch(self, agent: str, prompt: str, requested_by: str) -> str:
        did = str(uuid.uuid4())
        self.dispatches[did] = {
            "agent": agent,
            "prompt": prompt,
            "requested_by": requested_by,
            "status": "running",
        }
        return did

    def finish_dispatch(self, dispatch_id: str, status: str, result: str) -> None:
        row = self.dispatches.get(dispatch_id)
        if row is not None:
            row["status"] = status
            row["result"] = result

    def audit(self, actor: str, action: str, target: str, detail: str) -> None:
        self.audits.append(
            {"actor": actor, "action": action, "target": target, "detail": detail}
        )


class SupabaseStore:  # pragma: no cover
    """Writes dispatch + audit rows to Supabase via PostgREST (service role)."""

    def __init__(self, url: str | None = None, key: str | None = None) -> None:
        import httpx

        self._url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self._key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self._http = httpx.Client(
            headers={
                "apikey": self._key,
                "Authorization": f"Bearer {self._key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

    def _post(self, table: str, row: dict) -> None:
        self._http.post(f"{self._url}/rest/v1/{table}", json=row)

    def start_dispatch(self, agent: str, prompt: str, requested_by: str) -> str:
        did = str(uuid.uuid4())
        self._post(
            "dispatch",
            {
                "id": did,
                "agent": agent,
                "prompt": prompt,
                "requested_by": requested_by,
                "status": "running",
            },
        )
        return did

    def finish_dispatch(self, dispatch_id: str, status: str, result: str) -> None:
        self._http.patch(
            f"{self._url}/rest/v1/dispatch?id=eq.{dispatch_id}",
            json={"status": status, "result_ref": result[:2000]},
        )

    def audit(self, actor: str, action: str, target: str, detail: str) -> None:
        self._post(
            "audit_log",
            {"actor": actor, "action": action, "target": target, "detail": detail},
        )
