"""Dispatcher settings, read from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _clean(v: str | None) -> str:
    return (v or "").strip()


def _flag(name: str) -> bool:
    return _clean(os.environ.get(name)).lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    secret: str
    allowlist: frozenset[str]
    container_prefix: str = "csuite-hermes-"
    max_turns: int = 40
    fake_docker: bool = False
    fake_store: bool = False


def load_settings() -> Settings:
    allow = _clean(os.environ.get("CSUITE_AGENT_ALLOWLIST", "rex,dash,closer,vault,bob,pulse"))
    return Settings(
        secret=_clean(os.environ.get("CSUITE_DISPATCHER_SECRET")),
        allowlist=frozenset(a for a in (x.strip() for x in allow.split(",")) if a),
        fake_docker=_flag("FAKE_DOCKER"),
        fake_store=_flag("FAKE_STORE"),
    )
