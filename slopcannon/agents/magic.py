"""The Magic-System Designer. Writes the `magic` section."""

from __future__ import annotations

from ..prompts import magic as P
from .base import Agent


class MagicSystem(Agent):
    name = "magic"
    section = "magic"

    ROLE = P.ROLE
    OUTPUT_CONTRACT = P.OUTPUT_CONTRACT
    TASK = P.TASK
