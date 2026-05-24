"""M9 / control C5: the leaked production secret must never appear here.

The deployable surface (infra, hermes, apps) must not reference
WORKER_SHARED_SECRET. Rotating it on production is a separate operator action
(docs/runbooks/secret-rotation.md); the C-Suite stack uses disjoint secrets.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCAN = ["infra", "hermes", "apps"]


def test_no_worker_shared_secret_in_deployable_surface():
    bad = []
    for d in SCAN:
        base = REPO / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix == ".md" or "tests" in p.parts:
                continue
            if "WORKER_SHARED_SECRET" in p.read_text(encoding="utf-8", errors="ignore"):
                bad.append(str(p.relative_to(REPO)))
    assert not bad, f"WORKER_SHARED_SECRET must not appear in: {bad}"
