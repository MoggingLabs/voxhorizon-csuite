"""Agent name validation: the second layer of the C2 control.

Only a bare lowercase agent name on the allow-list resolves to a container. The
name is never interpolated into a shell; exec uses an argv array.
"""

from __future__ import annotations

import re

from .config import Settings

_AGENT_RE = re.compile(r"^[a-z]+$")


def resolve_container(agent: str, settings: Settings) -> str:
    if not _AGENT_RE.fullmatch(agent or ""):
        raise ValueError("invalid agent name")
    if agent not in settings.allowlist:
        raise ValueError("agent not allowed")
    return settings.container_prefix + agent
