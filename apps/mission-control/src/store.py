"""Read-side store for the history view. FakeStore for CI; SupabaseStore in prod."""

from __future__ import annotations

import os
from typing import Protocol


class Store(Protocol):
    def recent_dispatches(self, limit: int = 20) -> list[dict]: ...
    def recent_audits(self, limit: int = 20) -> list[dict]: ...


class FakeStore:
    def __init__(self, dispatches: list[dict] | None = None, audits: list[dict] | None = None) -> None:
        self._d = dispatches or []
        self._a = audits or []

    def recent_dispatches(self, limit: int = 20) -> list[dict]:
        return self._d[:limit]

    def recent_audits(self, limit: int = 20) -> list[dict]:
        return self._a[:limit]


class SupabaseStore:  # pragma: no cover
    def __init__(self, url: str | None = None, key: str | None = None) -> None:
        import httpx

        self._url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self._http = httpx.Client(
            headers={"apikey": key, "Authorization": f"Bearer {key}"}, timeout=10
        )

    def _get(self, table: str, limit: int) -> list[dict]:
        r = self._http.get(
            f"{self._url}/rest/v1/{table}",
            params={"select": "*", "order": "created_at.desc", "limit": limit},
        )
        return r.json() if r.status_code == 200 else []

    def recent_dispatches(self, limit: int = 20) -> list[dict]:
        return self._get("dispatch", limit)

    def recent_audits(self, limit: int = 20) -> list[dict]:
        return self._get("audit_log", limit)
