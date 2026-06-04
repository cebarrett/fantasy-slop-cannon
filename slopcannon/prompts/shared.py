"""Prompt fragments shared by every worker agent.

The collaboration rules are the consistency-pressure lever: this is the text
that tells each agent the bible is canonical and locked. Whether agents actually
honor it is exactly the kind of coordination failure this project exists to
observe, so it lives in one place where we can tune it deliberately.
"""

from __future__ import annotations

from ..bible import StoryBible

# Goes in the system prompt of every worker, between its ROLE and OUTPUT_CONTRACT.
COLLABORATION_RULES = """You are one agent on a team writing a single fantasy short story together. \
The team works by building up a shared "story bible" one section at a time. Earlier agents wrote the \
sections you will see; later agents will build on what you write now.

Two rules govern your contribution:
1. Everything already in the bible is CANONICAL and LOCKED. Do not contradict it, and do not rewrite, \
restate, or "improve" another agent's section. Build on what is there.
2. Produce ONLY your own section's content — no preamble, no meta-commentary, no section heading naming \
yourself, no notes to teammates. Just the prose/markdown that belongs in your section, ready to drop in."""


def bible_block(bible: StoryBible) -> str:
    """The 'here is the story so far' block for a worker's user message."""
    return f"Here is the story bible so far:\n\n---\n{bible.render()}\n---"
