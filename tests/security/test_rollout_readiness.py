"""M7 rollout readiness: every agent is wired end to end.

Static proof that each agent has a persona and is present in every layer that has
to know about it (Hermes compose, dispatcher allow-list both in compose and code,
and the Mission Control roster). The live per-agent dispatch (real LLM output)
is verified on the VPS at deploy.
"""

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
AGENTS = ["rex", "dash", "closer", "vault", "bob", "pulse"]


def test_every_agent_has_a_soul():
    for a in AGENTS:
        assert (REPO / "hermes" / "agents" / a / "SOUL.md").exists(), a


def test_every_agent_is_a_hermes_service():
    data = yaml.safe_load((REPO / "infra" / "docker-compose.hermes.yml").read_text(encoding="utf-8"))
    services = set(data.get("services", {}))
    assert {f"csuite-hermes-{a}" for a in AGENTS} <= services


def test_dispatcher_allowlist_compose_and_code():
    disp = yaml.safe_load((REPO / "infra" / "docker-compose.dispatcher.yml").read_text(encoding="utf-8"))
    allow = set(str(disp["services"]["csuite-dispatcher"]["environment"]["CSUITE_AGENT_ALLOWLIST"]).split(","))
    assert allow == set(AGENTS)
    code = (REPO / "apps" / "csuite-dispatcher" / "src" / "config.py").read_text(encoding="utf-8")
    for a in AGENTS:
        assert a in code


def test_mission_control_roster_lists_every_agent():
    code = (REPO / "apps" / "mission-control" / "src" / "config.py").read_text(encoding="utf-8")
    for a in AGENTS:
        assert f'"{a}"' in code
