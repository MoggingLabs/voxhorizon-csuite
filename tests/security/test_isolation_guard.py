"""Unit tests for the static isolation guard (control C1/C6).

Proves the guard both passes clean trees and CATCHES each forbidden pattern, and
that it correctly skips comments, markdown, and tests directories.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import isolation_guard as ig  # noqa: E402


def _write(tmp: Path, rel: str, content: str) -> None:
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_clean_tree(tmp_path):
    _write(tmp_path, "infra/x.yml", "services:\n  a:\n    image: ok\n")
    assert ig.scan(tmp_path) == []


def test_detects_openrouter_endpoint(tmp_path):
    _write(tmp_path, "infra/x.yml", "    base_url: https://openrouter.ai/api/v1\n")
    assert ig.scan(tmp_path)


def test_detects_prod_network(tmp_path):
    _write(tmp_path, "infra/x.yml", "    name: voxhorizon_default\n")
    assert ig.scan(tmp_path)


def test_detects_prod_container(tmp_path):
    _write(tmp_path, "hermes/x.sh", "docker exec hermes-agent-ekko sh\n")
    assert ig.scan(tmp_path)


def test_detects_api_key_assignment(tmp_path):
    _write(tmp_path, "infra/x.env", "OPENAI_API_KEY=sk-not-a-real-key-123\n")
    assert ig.scan(tmp_path)


def test_detects_prod_path(tmp_path):
    _write(tmp_path, "infra/x.sh", "cp file /opt/voxhorizon/.env\n")
    assert ig.scan(tmp_path)


def test_skips_comment_lines(tmp_path):
    _write(tmp_path, "infra/x.yml", "# never join voxhorizon_default here\n")
    assert ig.scan(tmp_path) == []


def test_skips_markdown(tmp_path):
    _write(tmp_path, "infra/x.md", "the old base_url was https://openrouter.ai/v1\n")
    assert ig.scan(tmp_path) == []


def test_skips_tests_dir(tmp_path):
    _write(tmp_path, "apps/foo/tests/test_x.py", "BAD = 'voxhorizon_default'\n")
    assert ig.scan(tmp_path) == []
