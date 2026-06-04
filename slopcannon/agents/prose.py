"""The Prose Writer. Writes the `prose` section (the actual story)."""

from __future__ import annotations

from ..prompts import prose as P
from .base import Agent


class ProseWriter(Agent):
    name = "prose"
    section = "prose"

    ROLE = P.ROLE
    OUTPUT_CONTRACT = P.OUTPUT_CONTRACT
    TASK = P.TASK
