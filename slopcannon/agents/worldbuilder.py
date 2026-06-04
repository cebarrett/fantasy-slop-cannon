"""The Worldbuilder — first worker in the pipeline. Writes the `world` section."""

from __future__ import annotations

from ..prompts import worldbuilder as P
from .base import Agent


class Worldbuilder(Agent):
    name = "worldbuilder"
    section = "world"

    ROLE = P.ROLE
    OUTPUT_CONTRACT = P.OUTPUT_CONTRACT
    TASK = P.TASK
