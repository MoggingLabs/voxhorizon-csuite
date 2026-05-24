"""Port-binding isolation test (control C1): sec_ports_loopback_only.

Every host port published by our compose files must bind to 127.0.0.1, so nothing
is exposed beyond the loopback interface (public access is via Tailscale Serve).
"""

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
INFRA = REPO / "infra"


def test_host_ports_are_loopback_only():
    bad = []
    for f in sorted(INFRA.glob("docker-compose*.yml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for svc, cfg in (data.get("services") or {}).items():
            cfg = cfg or {}
            for p in cfg.get("ports") or []:
                if not str(p).startswith("127.0.0.1:"):
                    bad.append(f"{f.name}:{svc}: {p}")
    assert not bad, f"non-loopback host ports found: {bad}"
