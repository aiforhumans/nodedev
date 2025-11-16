"""Shared helpers for LM Studio backed nodes."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .info import InfoFormatter
from .node_base import XtremetoolsBaseNode


class LMStudioAPIError(RuntimeError):
    """Raised when LM Studio cannot satisfy a request."""


@dataclass(slots=True)
class LMStudioResult:
    text: str
    model: str | None
    finish_reason: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    latency_ms: float


class LMStudioBaseNode(XtremetoolsBaseNode):
    """Base node with HTTP utilities for LM Studio chat endpoints."""

    CATEGORY = "Xtremetools/LM Studio"
    DEFAULT_SERVER_URL = "http://localhost:1234"
    DEFAULT_TIMEOUT = 60

    @staticmethod
    def build_messages(prompt: str, user_input: str = "", system_prompt: str | None = None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt.strip()})
        if user_input.strip():
            messages.append({"role": "user", "content": user_input.strip()})
        return messages

    def invoke_chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        server_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
        timeout: int | float | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LMStudioResult:
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": response_format or {"type": "text"},
        }
        if model:
            payload["model"] = model

        base_url = (server_url or self.DEFAULT_SERVER_URL).rstrip("/")
        endpoint = f"{base_url}/v1/chat/completions"
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        start = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=timeout or self.DEFAULT_TIMEOUT) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:  # pragma: no cover - HTTP error responses
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8", errors="ignore")
            except Exception:  # pragma: no cover - best-effort only
                error_body = ""

            detail: str | None = None
            if error_body:
                try:
                    parsed = json.loads(error_body)
                    if isinstance(parsed, dict):
                        detail = parsed.get("error") or json.dumps(parsed)
                    else:
                        detail = str(parsed)
                except json.JSONDecodeError:
                    detail = error_body.strip()

            raise LMStudioAPIError(
                f"HTTP {exc.code} from LM Studio: {detail or exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network issues
            raise LMStudioAPIError(f"Failed to reach LM Studio at {endpoint}: {exc}") from exc

        latency_ms = (time.perf_counter() - start) * 1000

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:  # pragma: no cover - invalid JSON
            raise LMStudioAPIError("LM Studio returned invalid JSON") from exc

        if "error" in payload:
            raise LMStudioAPIError(str(payload["error"]))

        choices = payload.get("choices") or []
        if not choices:
            raise LMStudioAPIError("LM Studio returned no choices")

        message = choices[0].get("message", {})
        text = message.get("content", "").strip()
        finish_reason = choices[0].get("finish_reason")
        usage = payload.get("usage", {})

        return LMStudioResult(
            text=text,
            model=payload.get("model"),
            finish_reason=finish_reason,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            latency_ms=latency_ms,
        )

    def build_completion_info(self, result: LMStudioResult) -> str:
        formatter = InfoFormatter(title="LM Studio", emoji="🤖")
        formatter.add(f"Model: {result.model or 'default'}")
        formatter.add(f"Finish reason: {result.finish_reason or 'unknown'}")
        formatter.add(
            f"Tokens (prompt/completion): {result.prompt_tokens or 0}/{result.completion_tokens or 0}"
        )
        formatter.add(f"Latency: {result.latency_ms:.1f} ms")
        return formatter.render()
