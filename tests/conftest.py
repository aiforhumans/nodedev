"""Shared pytest fixtures for Xtremetools tests."""
from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path
from typing import Any, Deque, Iterable

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "Xtremetools" / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from comfyui_xtremetools.base import lm_studio as lm_module


class _FakeLMStudioResponse:
    def __init__(self, payload: Any):
        self._payload = payload

    def __enter__(self) -> "_FakeLMStudioResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001
        return False

    def read(self) -> bytes:
        if isinstance(self._payload, bytes):
            return self._payload
        return json.dumps(self._payload).encode("utf-8")


class FakeLMStudioServer:
    """Queues deterministic responses for urllib.request.urlopen."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._responses: Deque[Any] = deque()
        self.requests: list[dict[str, Any]] = []

        def _fake_urlopen(request, timeout=None):  # noqa: ANN001
            if not self._responses:
                raise AssertionError("No fake LM Studio responses queued")

            payload = self._responses.popleft()
            body = json.loads(request.data.decode("utf-8"))
            self.requests.append(
                {
                    "url": request.full_url,
                    "timeout": timeout,
                    "body": body,
                }
            )

            if isinstance(payload, Exception):
                raise payload
            return _FakeLMStudioResponse(payload)

        monkeypatch.setattr(lm_module.urllib.request, "urlopen", _fake_urlopen)

    def queue(self, *responses: Any) -> None:
        if not responses:
            raise ValueError("Provide at least one fake LM Studio response")
        self._responses.extend(responses)


@pytest.fixture
def fake_lm_studio_server(monkeypatch: pytest.MonkeyPatch) -> FakeLMStudioServer:
    """Fixture that patches LM Studio HTTP calls with queued responses."""

    server = FakeLMStudioServer(monkeypatch)
    return server


@pytest.fixture
def workflow_builder() -> Any:
    """Builds canonical ComfyUI workflow dictionaries with overrides."""

    def _builder(**overrides: Any) -> dict[str, Any]:
        workflow: dict[str, Any] = {
            "last_node_id": 0,
            "last_link_id": 0,
            "nodes": [],
            "links": [],
            "groups": [],
        }
        workflow.update(overrides)
        return workflow

    return _builder


@pytest.fixture(scope="session")
def alias_iterator() -> Iterable[tuple[str, type[Any]]]:
    """Iterates over the node registry discovered via alias.py."""

    from comfyui_xtremetools.alias import NODE_CLASS_MAPPINGS

    return tuple(NODE_CLASS_MAPPINGS.items())


@pytest.fixture(scope="session")
def alias_display_names() -> dict[str, str]:
    from comfyui_xtremetools.alias import NODE_DISPLAY_NAME_MAPPINGS

    return NODE_DISPLAY_NAME_MAPPINGS


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-node-snapshots",
        action="store_true",
        help="Rewrite node contract snapshots under tests/snapshots/node_contracts",
    )


@pytest.fixture(scope="session")
def update_node_snapshots(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--update-node-snapshots"))
