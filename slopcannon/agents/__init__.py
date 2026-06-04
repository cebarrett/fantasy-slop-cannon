"""Agents — the producers and the judge.

Each worker subclasses Agent (base.py), supplies its ROLE / OUTPUT_CONTRACT /
TASK from the matching prompts module, and produces one section of the bible.
Agents are pure: run() returns a contribution string and never mutates shared
state. The orchestrator (the editor-in-chief) is what commits contributions to
the bible — agents propose, the editor commits.

PIPELINE is the canonical worker order; the orchestrator runs them in this
sequence, each reading everything the previous ones committed.
"""

from .base import Agent
from .character import CharacterDesigner
from .judge import ConsistencyJudge
from .magic import MagicSystem
from .plot import PlotArchitect
from .prose import ProseWriter
from .worldbuilder import Worldbuilder

# Worker classes in execution order. The judge is intentionally NOT in PIPELINE:
# it is an advisory reviewer, not a producer stage.
PIPELINE = [Worldbuilder, MagicSystem, CharacterDesigner, PlotArchitect, ProseWriter]

__all__ = [
    "Agent",
    "Worldbuilder",
    "MagicSystem",
    "CharacterDesigner",
    "PlotArchitect",
    "ProseWriter",
    "ConsistencyJudge",
    "PIPELINE",
]
