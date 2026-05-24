"""Client to the dispatcher. FakeDispatcher for CI; HttpDispatcher in production."""

from __future__ import annotations

from typing import Iterator, Protocol


class DispatcherClient(Protocol):
    def stream(self, agent: str, prompt: str) -> Iterator[str]: ...


class FakeDispatcher:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def stream(self, agent: str, prompt: str) -> Iterator[str]:
        self.calls.append((agent, prompt))
        yield f"data: dispatched {agent}\n\n"
        yield f"data: {prompt}\n\n"


class HttpDispatcher:  # pragma: no cover
    def __init__(self, url: str, secret: str) -> None:
        self._url = url.rstrip("/")
        self._secret = secret

    def stream(self, agent: str, prompt: str) -> Iterator[str]:
        import httpx

        with httpx.Client(timeout=None) as c:
            with c.stream(
                "POST",
                f"{self._url}/dispatch",
                json={"agent": agent, "prompt": prompt},
                headers={"Authorization": f"Bearer {self._secret}"},
            ) as r:
                for chunk in r.iter_text():
                    yield chunk
