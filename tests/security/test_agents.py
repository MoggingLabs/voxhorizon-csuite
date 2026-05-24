"""M4 agent consistency tests (controls C1, C2, C4).

Static proofs that every agent is passive (no listening gateway), has a persona,
and matches the dispatcher allow-list. The live fault-isolation proof (kill one,
others survive) runs on the VPS.
"""

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
AGENTS = ["rex", "dash", "closer", "vault", "bob", "pulse"]


def _load(name):
    return yaml.safe_load((REPO / "infra" / name).read_text(encoding="utf-8"))


def test_agents_are_passive():
    data = _load("docker-compose.hermes.yml")
    anchor = data.get("x-hermes-agent", {})
    assert anchor.get("command") == ["sleep", "infinity"]
    assert anchor.get("restart") == "unless-stopped"


def test_all_agents_present_as_services():
    data = _load("docker-compose.hermes.yml")
    services = set(data.get("services", {}).keys())
    assert services == {f"csuite-hermes-{a}" for a in AGENTS}


def test_every_agent_has_a_soul_without_em_dash():
    for a in AGENTS:
        soul = REPO / "hermes" / "agents" / a / "SOUL.md"
        assert soul.exists(), f"missing SOUL for {a}"
        text = soul.read_text(encoding="utf-8")
        assert text.strip(), f"empty SOUL for {a}"
        assert "—" not in text, f"em dash in {a} SOUL"


def test_dispatcher_allowlist_matches_agents():
    data = _load("docker-compose.dispatcher.yml")
    env = data["services"]["csuite-dispatcher"]["environment"]
    allow = set(str(env["CSUITE_AGENT_ALLOWLIST"]).split(","))
    assert allow == set(AGENTS)
