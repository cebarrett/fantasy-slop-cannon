"""The Editor-in-Chief — the top of the (currently shallow) hierarchy.

In the MVP the editor's job is deliberately thin: expand the premise, run the
worker pipeline in order, and — crucially — be the *single place* where
contributions become canonical truth. Every section the team produces is written
to the bible through one method, `commit()`, which normalizes the contribution
first. That single seam is where the authority/consistency machinery will grow
in later versions; right now it just strips the redundant section heading the
workers keep emitting (the Phase 3 finding).

The editor is library code: it never reads argv or prints on its own. The CLI
passes a `log` callback for progress; by default it is silent.
"""

from __future__ import annotations

import re
from typing import Callable

from .agents import PIPELINE
from .bible import SECTION_TITLES, StoryBible
from .client import ModelClient
from .config import AgentConfig, get_config
from .prompts import editor as editor_prompts
from .runlog import RunLogger

# Matches a single leading ATX heading line, capturing its text.
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")


def normalize_contribution(section: str, text: str) -> str:
    """Strip a leading heading the model emitted that merely names its own
    section (e.g. a worker prefixing its output with '## Magic System' even
    though render() already adds that heading). Only a heading whose text
    matches the section's title or key is removed, so genuine sub-headings and
    real story titles are left untouched.
    """
    text = text.strip()
    lines = text.split("\n")

    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return text

    match = _HEADING_RE.match(lines[i])
    if match:
        heading_text = match.group(1).strip().lower()
        targets = {SECTION_TITLES.get(section, "").lower(), section.lower()}
        if heading_text in targets:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            lines = lines[:i] + lines[j:]
    return "\n".join(lines).strip()


class EditorInChief:
    """Owns the bible, sequences the pipeline, commits canonical truth."""

    def __init__(
        self,
        client: ModelClient,
        logger: RunLogger,
        *,
        expand_premise: bool = True,
        agent_configs: dict[str, AgentConfig] | None = None,
        log: Callable[[str], None] = lambda _msg: None,
    ) -> None:
        self.client = client
        self.logger = logger
        self.expand_premise = expand_premise
        self.agent_configs = agent_configs or {}
        self.log = log
        self.bible = StoryBible()

    # -- the one place canonical truth is written -----------------------------

    def commit(self, section: str, contribution: str) -> None:
        """Normalize a contribution, then commit it to the bible. Single seam."""
        self.bible.set(section, normalize_contribution(section, contribution))

    def _config_for(self, name: str) -> AgentConfig:
        return self.agent_configs.get(name) or get_config(name)

    # -- stages ---------------------------------------------------------------

    def generate_premise(self) -> str:
        """Have the editor invent a one-line fantasy premise from nothing."""
        cfg = self._config_for("editor")
        self.log(f"editor: generating a premise ({cfg.model}) ...")
        result = self.client.call(
            cfg,
            system=editor_prompts.GENERATE_SYSTEM,
            user=editor_prompts.GENERATE_TASK,
        )
        premise = result.text.strip()
        self.log(f"editor: generated premise -> {premise}")
        return premise

    def establish_premise(self, raw_premise: str | None) -> None:
        """Commit the premise, expanding it via one editor call unless disabled.

        When raw_premise is None, the editor first invents the one-line premise,
        which then flows through the same expansion path.
        """
        if raw_premise is None:
            raw_premise = self.generate_premise()
        if not self.expand_premise:
            self.log("editor: using raw premise (expansion disabled)")
            self.commit("premise", raw_premise)
            return
        cfg = self._config_for("editor")
        self.log(f"editor: expanding premise ({cfg.model}) ...")
        result = self.client.call(
            cfg,
            system=editor_prompts.SYSTEM,
            user=editor_prompts.premise_task(raw_premise),
        )
        self.commit("premise", result.text)

    def run_pipeline(self) -> None:
        """Run each worker in order; commit each contribution as it lands."""
        for AgentClass in PIPELINE:
            cfg = self._config_for(AgentClass.name)
            agent = AgentClass(cfg)
            self.log(f"{agent.name}: writing '{agent.section}' ({agent.config.model}) ...")
            contribution = agent.run(self.bible, self.client)
            self.commit(agent.section, contribution)
            self.log(f"{agent.name}: committed {len(self.bible.get(agent.section))} chars")

    def write_artifacts(self) -> None:
        """Write the canonical bible + story as markdown and HTML reading copies."""
        self.logger.write_artifact("bible.md", self.bible.render())
        self.logger.write_artifact("story.md", self.bible.get("prose"))
        self.logger.write_html("story.html", "The Story", self.bible.get("prose"))
        self.logger.write_html("bible.html", "Story Bible", self.bible.render())

    # -- the whole run --------------------------------------------------------

    def run(self, raw_premise: str | None) -> StoryBible:
        """Premise -> full pipeline -> artifacts. Returns the finished bible.

        Pass raw_premise=None to have the editor generate the premise itself.
        """
        self.establish_premise(raw_premise)
        self.run_pipeline()
        self.write_artifacts()
        self.log(f"done -> {self.logger.dir}")
        return self.bible
