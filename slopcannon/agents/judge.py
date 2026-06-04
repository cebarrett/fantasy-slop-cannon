"""The Consistency Judge — an advisory reviewer, not a producer.

Unlike the worker agents, the judge reads the *full* bible (including the prose),
writes no section, and its output is never committed to canonical truth. So it
deliberately does NOT subclass Agent or reuse the worker collaboration rules —
it is a different shape, and keeping it separate keeps that distinction explicit.
"""

from __future__ import annotations

from ..bible import StoryBible
from ..client import ModelClient
from ..config import AgentConfig, get_config
from ..prompts import judge as P


class ConsistencyJudge:
    name = "judge"

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or get_config(self.name)

    def run(self, bible: StoryBible, client: ModelClient) -> str:
        """Read the full bible + prose, return a consistency report (markdown).

        Advisory: the caller prints/saves this but never commits it.
        """
        result = client.call(
            self.config,
            system=P.SYSTEM,
            user=P.task(bible.render()),
        )
        return result.text
