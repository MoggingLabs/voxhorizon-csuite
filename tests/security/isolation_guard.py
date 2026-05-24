#!/usr/bin/env python3
"""Static isolation guard (security control C1 / C6): sec_isolation_static.

Fails if the DEPLOYABLE surface (infra/, hermes/, apps/) references the production
stack or reintroduces OpenRouter / an OpenAI API key. This is the repo-wide guard
that keeps the C-Suite isolated from production by construction.

Rules:
- Scan infra/, hermes/, apps/ only (not docs/ or tests/, which legitimately name
  forbidden tokens in prose or negative test fixtures).
- Skip .md files (documentation may name what must not be touched).
- Skip comment lines (a comment that says "never join voxhorizon_default" is fine).
- Flag actual usage: a prod network/container/path, an `openrouter.ai` endpoint,
  or an `OPENAI_API_KEY` / `OPENROUTER_API_KEY` assignment with a value.

Run: python tests/security/isolation_guard.py  (exit 1 on any finding)
Importable: scan(root) -> list[str] of findings, used by the unit tests.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCAN_DIRS = ["infra", "hermes", "apps"]
SKIP_SUFFIXES = {".md"}
SKIP_DIR_PARTS = {"tests", "__pycache__", "node_modules", ".venv"}

FORBIDDEN = [
    (re.compile(r"voxhorizon_default"), "production docker network"),
    (re.compile(r"hermes-agent-ekko"), "production Hermes container"),
    (re.compile(r"openrouter\.ai", re.IGNORECASE), "OpenRouter endpoint (use the Codex subscription)"),
    (re.compile(r"OPENAI_API_KEY\s*=\s*\S"), "OpenAI API key assignment (subscription only)"),
    (re.compile(r"OPENROUTER_API_KEY\s*=\s*\S"), "OpenRouter API key assignment"),
    (re.compile(r"/opt/voxhorizon/"), "production path (use /opt/voxhorizon-csuite)"),
]


def is_comment(line: str) -> bool:
    s = line.lstrip()
    return s.startswith("#") or s.startswith("//")


def iter_files(root: Path):
    for d in SCAN_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix in SKIP_SUFFIXES:
                continue
            if any(part in SKIP_DIR_PARTS for part in p.parts):
                continue
            yield p


def scan(root: Path) -> list[str]:
    """Return a list of findings (file:line: why: snippet). Empty means clean."""
    findings: list[str] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if is_comment(line):
                continue
            for pat, why in FORBIDDEN:
                if pat.search(line):
                    rel = path.relative_to(root)
                    findings.append(f"{rel}:{n}: {why}: {line.strip()[:120]}")
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    findings = scan(root)
    if findings:
        print("ISOLATION GUARD FAILED:")
        for f in findings:
            print("  " + f)
        return 1
    print("isolation guard: clean (no production refs, no OpenRouter, no API keys)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
