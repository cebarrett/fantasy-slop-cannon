"""The Character Designer. Writes the `characters` section."""

from __future__ import annotations

from ..prompts import character as P
from .base import Agent


class CharacterDesigner(Agent):
    name = "character"
    section = "characters"

    ROLE = P.ROLE
    OUTPUT_CONTRACT = P.OUTPUT_CONTRACT
    TASK = P.TASK
