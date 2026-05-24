"""Ingest runner: pull -> normalize -> validate -> upsert, per connector.

Runs as a batch worker (cron / `docker compose run`), not a web service. In CI
it runs against FAKE source payloads and a FakeStore, so there are no network
calls and no credentials. A failure in one connector is isolated: it is recorded
and the runner moves on, so one broken source never blocks the rest.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from .config import Settings, load_settings
from .connectors import REGISTRY
from .store import FakeStore, Store


@dataclass
class Result:
    connector: str
    table: str
    rows: int
    ok: bool
    error: str = ""


def _validate(connector, rows: list[dict]) -> None:
    for row in rows:
        extra = set(row) - set(connector.columns)
        if extra:
            raise ValueError(f"{connector.source}: unknown columns {sorted(extra)}")
        if connector.pk not in row or row[connector.pk] in (None, ""):
            raise ValueError(f"{connector.source}: row missing pk '{connector.pk}'")


def _raw_for(connector, settings: Settings, store: Store, env: dict) -> list[dict]:
    if settings.fake_source:
        return connector.fake_raw()
    if connector.internal:
        return connector.read_source(store)
    return connector.fetch(env)


def run(
    settings: Settings,
    store: Store,
    names: list[str] | None = None,
    env: dict | None = None,
) -> list[Result]:
    env = env if env is not None else dict(os.environ)
    selected = names or list(REGISTRY)
    results: list[Result] = []
    for name in selected:
        connector = REGISTRY[name]()
        try:
            raw = _raw_for(connector, settings, store, env)
            rows = connector.normalize(raw)
            _validate(connector, rows)
            n = store.upsert(connector.table, rows, connector.pk)
            results.append(Result(name, connector.table, n, True))
        except Exception as exc:  # isolate per-connector failure
            results.append(Result(name, connector.table, 0, False, str(exc)))
    return results


def _build_store(settings: Settings) -> Store:
    if settings.fake_store:
        return FakeStore()
    from .store import SupabaseStore  # pragma: no cover

    return SupabaseStore(settings.supabase_url, settings.supabase_key)  # pragma: no cover


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    settings = load_settings()
    store = _build_store(settings)
    results = run(settings, store, names=argv or None)
    failed = 0
    for r in results:
        status = "ok" if r.ok else "FAIL"
        line = f"{status:4} {r.connector:18} {r.table:18} rows={r.rows}"
        if not r.ok:
            line += f"  {r.error}"
            failed += 1
        print(line)
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
