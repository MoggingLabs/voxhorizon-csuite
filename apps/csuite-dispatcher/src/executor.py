"""Executors run `hermes chat` in a target container and stream the output.

FakeExecutor is used in CI (FAKE_DOCKER) so tests need no Docker daemon.
RealExecutor talks to the scope-limited docker-socket-proxy via the Docker SDK
(DOCKER_HOST), executing an argv array (never a shell string).
"""

from __future__ import annotations

import os
from typing import Iterator, List, Protocol


class Executor(Protocol):
    def run(self, container: str, argv: List[str]) -> Iterator[str]: ...


class FakeExecutor:
    """Records exec calls and yields deterministic, credential-free output."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def run(self, container: str, argv: List[str]) -> Iterator[str]:
        self.calls.append((container, list(argv)))
        prompt = argv[3] if len(argv) > 3 else ""
        yield f"[fake] exec in {container}\n"
        yield f"[fake] prompt: {prompt}\n"
        yield "[fake] done\n"


class RealExecutor:  # pragma: no cover
    """Streams `docker exec` output through the scoped proxy (DOCKER_HOST)."""

    def __init__(self, base_url: str | None = None) -> None:
        import docker

        self._client = docker.DockerClient(
            base_url=base_url or os.environ.get("DOCKER_HOST", "")
        )

    def run(self, container: str, argv: List[str]) -> Iterator[str]:
        c = self._client.containers.get(container)
        _, stream = c.exec_run(argv, stream=True, demux=False)
        for chunk in stream:
            yield chunk.decode("utf-8", "replace")
