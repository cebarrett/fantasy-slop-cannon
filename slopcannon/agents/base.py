"""The Agent base class — the backbone every worker inherits.

A worker is defined almost entirely by three strings (ROLE, OUTPUT_CONTRACT,
TASK) plus which bible section it writes. The base composes those with the
shared collaboration rules into a system prompt, builds the user message from
the current bible, makes one logged model call, and returns the contribution.

Agents are intentionally pure with respect to shared state: run() returns text
and does not touch the bible. Committing is the editor-in-chief's job, which
keeps "who owns the canonical truth" a single, explicit place in the system.
"""

from __future__ import annotations

from ..bible import StoryBible
from ..client import ModelClient
from ..config import AgentConfig, get_config
from ..prompts.shared import COLLABORATION_RULES, bible_block


class Agent:
    # Subclasses set these. `name` keys the config; `section` is the bible
    # section this agent writes (usually the same word).
    name: str
    section: str

    # Subclasses provide these prompt fragments (typically from a prompts module).
    ROLE: str
    OUTPUT_CONTRACT: str
    TASK: str

    def __init__(self, config: AgentConfig | None = None) -> None:
        # Default to this agent's configured model; allow an override for
        # experiments (e.g. running the worldbuilder on Opus).
        self.config = config or get_config(self.name)

    def system_prompt(self) -> str:
        """Role + shared collaboration rules + this agent's output contract."""
        return f"{self.ROLE}\n\n{COLLABORATION_RULES}\n\n{self.OUTPUT_CONTRACT}"

    def user_message(self, bible: StoryBible) -> str:
        """The current bible followed by this agent's specific task."""
        return f"{bible_block(bible)}\n\n{self.TASK}"

    def run(self, bible: StoryBible, client: ModelClient) -> str:
        """Make one logged model call and return this agent's contribution.

        Does not mutate the bible — the caller commits the returned text.
        """
        result = client.call(
            self.config,
            system=self.system_prompt(),
            user=self.user_message(bible),
        )
        return result.text

    def revise(self, bible: StoryBible, client: ModelClient, findings_text: str) -> str:
        """Re-produce this agent's section to resolve flagged contradictions.

        The agent sees the current (locked) bible plus the consistency problems
        about its section, and may freely rewrite ONLY its own section while
        keeping everything else fixed. Returns the revised section text.
        """
        user = (
            f"{bible_block(bible)}\n\n"
            f"Your '{self.section}' section has been flagged for the following consistency problems:\n\n"
            f"{findings_text}\n\n"
            f"Revise ONLY your own '{self.section}' section to resolve these problems. You may rewrite your "
            f"section freely, but everything else in the bible above stays locked and must not change — make "
            f"your section consistent with it. Output only the revised section."
        )
        result = client.call(self.config, system=self.system_prompt(), user=user)
        return result.text
