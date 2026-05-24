"""Connector contract for the C-Suite ingests.

Each ingest is a Connector that pulls read-only from one source, normalizes the
raw payload into rows matching its Supabase table (0003_v2_ingest.sql), and lets
the runner upsert them. The normalized schema is the stable contract; only the
source-specific fetch() changes when the backing tool is chosen.

Design rules:
- fetch() is the only tool-specific surface. Until a source's tool is wired it
  raises NotImplementedError; the runner never calls it in FAKE mode.
- normalize() and fake_raw() are real now, so the schema is locked and tested.
- No connector ever writes; the runner owns persistence via the Store.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Connector(ABC):
    #: target table in the self-hosted Supabase (see db/migrations/0003_v2_ingest.sql)
    table: str = ""
    #: columns the connector may emit; normalize() output is validated against this
    columns: frozenset[str] = frozenset()
    #: primary-key column used for idempotent upserts
    pk: str = "id"
    #: stable source label written to every row
    source: str = ""
    #: internal connectors read from our own Supabase (e.g. audit_feed) instead of
    #: an external SaaS, so they need no credential and read via the Store.
    internal: bool = False

    @abstractmethod
    def normalize(self, raw: list[dict]) -> list[dict]:
        """Map raw source records to rows whose keys are a subset of `columns`."""

    @abstractmethod
    def fake_raw(self) -> list[dict]:
        """Deterministic sample payload for FAKE mode and tests (no network)."""

    def fetch(self, env: dict[str, str]) -> list[dict]:  # pragma: no cover
        """Pull raw records from the live source. Wired per chosen tool."""
        raise NotImplementedError(
            f"{self.source}: live connector not wired yet; runs in FAKE mode only"
        )

    def read_source(self, store) -> list[dict]:  # pragma: no cover
        """Internal connectors read their raw records from our own Store."""
        raise NotImplementedError(f"{self.source}: not an internal connector")
