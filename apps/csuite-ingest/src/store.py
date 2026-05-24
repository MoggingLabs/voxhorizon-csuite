"""Persistence for ingested rows.

FakeStore is an in-memory double for CI (FAKE_STORE). SupabaseStore upserts to
the self-hosted Supabase via PostgREST with the service role (server-side only),
resolving on the primary key so re-runs are idempotent.
"""

from __future__ import annotations

import os
from typing import Protocol


class Store(Protocol):
    def upsert(self, table: str, rows: list[dict], pk: str) -> int: ...
    def read(self, table: str, columns: str = "*") -> list[dict]: ...


class FakeStore:
    def __init__(self, seed: dict[str, list[dict]] | None = None) -> None:
        # table -> {pk_value: row}
        self.tables: dict[str, dict] = {}
        self.seed: dict[str, list[dict]] = seed or {}

    def upsert(self, table: str, rows: list[dict], pk: str) -> int:
        bucket = self.tables.setdefault(table, {})
        for row in rows:
            bucket[row[pk]] = row
        return len(rows)

    def read(self, table: str, columns: str = "*") -> list[dict]:
        return list(self.seed.get(table, []))


class SupabaseStore:  # pragma: no cover
    """Upserts/reads rows in Supabase via PostgREST (service role)."""

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
            timeout=30,
        )

    def upsert(self, table: str, rows: list[dict], pk: str) -> int:
        if not rows:
            return 0
        self._http.post(
            f"{self._url}/rest/v1/{table}",
            params={"on_conflict": pk},
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
            json=rows,
        )
        return len(rows)

    def read(self, table: str, columns: str = "*") -> list[dict]:
        resp = self._http.get(
            f"{self._url}/rest/v1/{table}", params={"select": columns}
        )
        return resp.json()
