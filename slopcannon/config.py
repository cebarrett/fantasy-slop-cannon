"""Per-agent configuration.

Every agent's model is configurable here so you can experiment. The defaults
follow the plan: stronger (Opus-class) models for the editor and judge, a
cheaper Sonnet-class default for the workers, with the prose writer bumped up
because it is the integration-heavy call.

These are plain data — importing this module makes no network calls and reads
no environment. Nothing here is agent logic; it is just the knobs.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

# Exact model IDs (see README for the family). Override per-agent below or at
# the call site by constructing/replacing an AgentConfig.
OPUS = "claude-opus-4-8"
SONNET = "claude-sonnet-4-6"
HAIKU = "claude-haiku-4-5-20251001"


@dataclass(frozen=True)
class AgentConfig:
    """Immutable knobs for a single agent's model call."""

    name: str
    model: str
    max_tokens: int
    # Optional: when None, temperature is omitted from the request entirely.
    # Opus 4.8 deprecates the parameter and rejects non-default values, so we
    # leave it unset by default and only opt in on models that support tuning.
    temperature: float | None = None

    def with_overrides(self, **changes) -> "AgentConfig":
        """Return a copy with some fields replaced (e.g. to swap the model)."""
        return replace(self, **changes)


# Canonical default config for each agent in the MVP. The orchestrator looks up
# agents by these keys. `max_tokens` is a ceiling, not a target; the prompt
# carries the actual length guidance. Temperature is left unset (model default);
# see AgentConfig.temperature for why.
DEFAULTS: dict[str, AgentConfig] = {
    "editor": AgentConfig("editor", OPUS, max_tokens=1024),
    "worldbuilder": AgentConfig("worldbuilder", SONNET, max_tokens=2048),
    "magic": AgentConfig("magic", SONNET, max_tokens=2048),
    "character": AgentConfig("character", SONNET, max_tokens=2048),
    "plot": AgentConfig("plot", SONNET, max_tokens=2048),
    "prose": AgentConfig("prose", OPUS, max_tokens=8192),
    "judge": AgentConfig("judge", OPUS, max_tokens=2048),
}


def get_config(name: str) -> AgentConfig:
    """Look up an agent's default config by name."""
    try:
        return DEFAULTS[name]
    except KeyError:
        raise KeyError(
            f"No default config for agent {name!r}. "
            f"Known agents: {', '.join(DEFAULTS)}"
        ) from None
