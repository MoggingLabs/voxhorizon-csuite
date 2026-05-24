"""Mission Control settings, read from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _clean(v: str | None) -> str:
    return (v or "").strip()


def _flag(name: str) -> bool:
    return _clean(os.environ.get(name)).lower() in ("1", "true", "yes")


_ROSTER = [
    ("rex", "COO / orchestrator"),
    ("dash", "Data and knowledge"),
    ("closer", "Sales"),
    ("vault", "Finance"),
    ("bob", "Marketing"),
    ("pulse", "Client success"),
]


@dataclass(frozen=True)
class Settings:
    auth_pass: str
    auth_secret: str
    dispatcher_url: str
    dispatcher_secret: str
    roster: list[tuple[str, str]] = field(default_factory=lambda: list(_ROSTER))
    fake_dispatcher: bool = False
    fake_store: bool = False


def load_settings() -> Settings:
    return Settings(
        auth_pass=_clean(os.environ.get("MC_AUTH_PASS")),
        auth_secret=_clean(os.environ.get("MC_AUTH_SECRET")),
        dispatcher_url=_clean(os.environ.get("CSUITE_DISPATCHER_URL", "http://csuite-dispatcher:8200")),
        dispatcher_secret=_clean(os.environ.get("CSUITE_DISPATCHER_SECRET")),
        fake_dispatcher=_flag("FAKE_DISPATCHER"),
        fake_store=_flag("FAKE_STORE"),
    )
