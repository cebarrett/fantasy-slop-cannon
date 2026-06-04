"""The Plot Architect. Writes the `plot` section (ordered scene beats)."""

from __future__ import annotations

from ..prompts import plot as P
from .base import Agent


class PlotArchitect(Agent):
    name = "plot"
    section = "plot"

    ROLE = P.ROLE
    OUTPUT_CONTRACT = P.OUTPUT_CONTRACT
    TASK = P.TASK
