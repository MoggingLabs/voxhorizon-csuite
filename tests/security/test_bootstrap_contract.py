"""Bootstrap isolation-contract tests (control C1).

sec_bootstrap_refuses_prod: the bootstrap refuses to run against the production
root. sec_dry_run_writes_nothing: --dry-run validates, prints a plan, exits 0
without root, and creates nothing.
"""

import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BOOT = REPO / "infra" / "bootstrap-csuite.sh"


def _run(args, root):
    env = dict(os.environ, CSUITE_ROOT=str(root))
    return subprocess.run(
        ["bash", str(BOOT), *args], env=env, capture_output=True, text=True
    )


def test_refuses_prod_root():
    r = _run([], "/opt/voxhorizon")
    assert r.returncode != 0
    assert "refus" in (r.stdout + r.stderr).lower()


def test_dry_run_writes_nothing(tmp_path):
    root = tmp_path / "csuite-root"
    r = _run(["--dry-run"], root)
    assert r.returncode == 0, r.stderr
    assert "dry run" in (r.stdout + r.stderr).lower()
    # The dry run must not create the root or any of its contents.
    assert not root.exists()
