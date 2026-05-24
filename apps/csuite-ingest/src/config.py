"""Ingest settings, read from the environment.

The runner needs only the Supabase target and the FAKE toggles. Each connector
reads its own source credential lazily inside fetch(), so a missing credential
keeps just that one source in mock mode without breaking the others.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _clean(v: str | None) -> str:
    return (v or "").strip()


def _flag(name: str) -> bool:
    return _clean(os.environ.get(name)).lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    fake_source: bool = False
    fake_store: bool = False


def load_settings() -> Settings:
    return Settings(
        supabase_url=_clean(os.environ.get("SUPABASE_URL")),
        supabase_key=_clean(os.environ.get("SUPABASE_SERVICE_ROLE_KEY")),
        fake_source=_flag("CSUITE_INGEST_FAKE_SOURCE"),
        fake_store=_flag("FAKE_STORE"),
    )
