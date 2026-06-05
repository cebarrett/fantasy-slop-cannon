"""Thin wrapper over the raw Anthropic SDK.

Every model call in the system goes through ModelClient.call(), which times the
call, extracts the text, and logs the full input/output via the RunLogger. The
client owns the call counter so traces are numbered in execution order and no
call can skip logging.

We use the raw `anthropic` SDK (not the Agent SDK) on purpose: for a learning
project the orchestration machinery is the point, and we don't want a framework
hiding the loop.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from anthropic import Anthropic

from .config import AgentConfig
from .runlog import RunLogger


@dataclass
class CallResult:
    """The text plus the metadata a caller might branch on."""

    text: str
    input_tokens: int | None
    output_tokens: int | None
    stop_reason: str | None
    latency_ms: int


def _extract_text(content_blocks) -> str:
    """Concatenate the text from a Messages response's content blocks."""
    parts = [block.text for block in content_blocks if getattr(block, "type", None) == "text"]
    return "".join(parts)


class ModelClient:
    """Wraps one Anthropic client + one run's logger."""

    def __init__(self, logger: RunLogger, *, api_key: str | None = None) -> None:
        # The SDK reads ANTHROPIC_API_KEY from the environment when api_key is
        # None; entry points are responsible for loading .env first.
        self._client = Anthropic(api_key=api_key)
        self._logger = logger
        self._n = 0

    def _base_kwargs(self, config: AgentConfig, system: str, user: str) -> dict:
        kwargs: dict = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        # Only send temperature when explicitly set; some models (e.g. Opus 4.8)
        # deprecate the parameter and reject non-default values.
        if config.temperature is not None:
            kwargs["temperature"] = config.temperature
        return kwargs

    def call(self, config: AgentConfig, *, system: str, user: str) -> CallResult:
        """Make one logged model call for the given agent config."""
        index = self._n
        self._n += 1

        started = time.monotonic()
        resp = self._client.messages.create(**self._base_kwargs(config, system, user))
        latency_ms = int((time.monotonic() - started) * 1000)

        text = _extract_text(resp.content)
        usage = getattr(resp, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        stop_reason = getattr(resp, "stop_reason", None)

        self._logger.log_call(
            index=index,
            agent=config.name,
            model=config.model,
            system=system,
            user=user,
            output=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            stop_reason=stop_reason,
        )

        return CallResult(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stop_reason=stop_reason,
            latency_ms=latency_ms,
        )

    def call_structured(self, config: AgentConfig, *, system: str, user: str, tool: dict) -> dict:
        """Make one logged call that forces the model to return structured data.

        `tool` is an Anthropic tool definition ({name, description, input_schema}).
        The model is forced to call it; we return the validated input dict. Logged
        like any other call, with the JSON output captured in the trace.
        """
        index = self._n
        self._n += 1

        kwargs = self._base_kwargs(config, system, user)
        kwargs["tools"] = [tool]
        kwargs["tool_choice"] = {"type": "tool", "name": tool["name"]}

        started = time.monotonic()
        resp = self._client.messages.create(**kwargs)
        latency_ms = int((time.monotonic() - started) * 1000)

        data: dict = {}
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                data = block.input
                break

        usage = getattr(resp, "usage", None)
        self._logger.log_call(
            index=index,
            agent=config.name,
            model=config.model,
            system=system,
            user=user,
            output=json.dumps(data, indent=2),
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            latency_ms=latency_ms,
            stop_reason=getattr(resp, "stop_reason", None),
        )
        return data
