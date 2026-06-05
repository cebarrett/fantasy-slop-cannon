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

from .agents import PIPELINE, ConsistencyJudge, Finding, render_report
from .bible import SECTION_ORDER, SECTION_TITLES, StoryBible
from .client import ModelClient
from .config import AgentConfig, get_config
from .prompts import editor as editor_prompts
from .runlog import RunLogger

# Matches a single leading ATX heading line, capturing its text.
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")

# Which agent owns (and can revise) each section. The premise is editor-owned and
# the judge is not a producer, so neither appears here.
SECTION_TO_AGENT = {cls.section: cls for cls in PIPELINE}

# Severities the revision pass acts on.
_ACTIONABLE = {"medium", "high"}


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
        judge: bool = True,
        revise: bool = False,
        agent_configs: dict[str, AgentConfig] | None = None,
        log: Callable[[str], None] = lambda _msg: None,
    ) -> None:
        self.client = client
        self.logger = logger
        self.expand_premise = expand_premise
        self.judge = judge
        self.revise = revise
        self.agent_configs = agent_configs or {}
        self.log = log
        self.bible = StoryBible()
        self.findings: list[Finding] | None = None          # judge pass before revision
        self.findings_after: list[Finding] | None = None    # judge pass after revision
        self.revised_sections: list[str] = []
        self.stale_sections: list[str] = []

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

    def _review(self, label: str) -> list[Finding]:
        """One judge pass over the current bible. Returns structured findings."""
        judge = ConsistencyJudge(self._config_for("judge"))
        self.log(f"judge ({label}): reviewing for contradictions ({judge.config.model}) ...")
        findings = judge.run(self.bible, self.client)
        n = len(findings)
        self.log(f"judge ({label}): {'clean' if n == 0 else f'flagged {n} contradiction(s)'}")
        return findings

    def run_judge(self) -> list[Finding] | None:
        """Initial advisory judge pass over the finished bible + prose."""
        if not self.judge:
            return None
        self.findings = self._review("initial")
        return self.findings

    # -- revision pass (canonicalization discipline lives here) ---------------

    def revise_section(self, section: str, new_text: str) -> None:
        """Replace a section's canonical truth IN PLACE, archiving the old one.

        The superseded version goes to the run log (never inline in the bible),
        and the bible is overwritten so downstream agents only ever see current
        truth. This is the one place canonical truth is *changed* rather than
        first written.
        """
        old = self.bible.get(section)
        self.logger.archive_revision(section, old)
        self.bible.set(section, normalize_contribution(section, new_text), overwrite=True)
        self.revised_sections.append(section)

    def _targets(self, findings: list[Finding]) -> dict[str, list[Finding]]:
        """Group actionable findings by the section that should change.

        Target = the most-downstream section named (foundational-first authority:
        earlier sections are more authoritative, so the later one conforms).
        """
        groups: dict[str, list[Finding]] = {}
        for f in findings:
            if f.severity not in _ACTIONABLE:
                continue
            sections = [s for s in f.sections if s in SECTION_TO_AGENT]
            if not sections:
                continue  # only implicates premise — editor-owned, skip in MVP
            target = max(sections, key=SECTION_ORDER.index)
            groups.setdefault(target, []).append(f)
        return groups

    def run_revision(self) -> None:
        """Single revision pass: fix each targeted section in place, then re-judge.

        Deliberately does NOT cascade. Revising a non-final section leaves the
        layers built on its old version stale; we detect and report that rather
        than re-running them (convergence is the next roadmap step).
        """
        if not self.revise or not self.findings:
            return
        groups = self._targets(self.findings)
        if not groups:
            self.log("revision: nothing actionable (no medium/high findings on a revisable section)")
            return

        # Revise in pipeline order for determinism.
        for section in SECTION_ORDER:
            if section not in groups:
                continue
            agent = SECTION_TO_AGENT[section](self._config_for(section))
            self.log(f"revision: revising '{section}' to resolve {len(groups[section])} finding(s) ...")
            revised = agent.revise(self.bible, self.client, render_report(groups[section]))
            self.revise_section(section, revised)

        self.stale_sections = self._stale_layers()
        if self.stale_sections:
            self.log(f"revision: STALE LAYERS introduced -> {', '.join(self.stale_sections)} (see revision_report.md)")

        # Re-judge so the effect of one pass is observable (still advisory).
        self.findings_after = self._review("re-check")

    def _stale_layers(self) -> list[str]:
        """Sections built on a now-superseded version of an earlier revised section.

        A section is stale if it comes after a revised section in the pipeline and
        was not itself revised (so it never saw the new version).
        """
        stale: set[str] = set()
        for revised in self.revised_sections:
            after = SECTION_ORDER[SECTION_ORDER.index(revised) + 1:]
            for later in after:
                if self.bible.has(later) and later not in self.revised_sections:
                    stale.add(later)
        return [s for s in SECTION_ORDER if s in stale]

    def _revision_report(self) -> str:
        lines = ["## Revision Report", ""]
        lines.append(f"Revised in place: {', '.join(self.revised_sections)}")
        lines.append("Superseded versions archived under `revisions/`.")
        lines.append("")
        if self.stale_sections:
            lines += [
                "### Potentially stale layers",
                "",
                "These sections were built on a now-superseded version of a section that was "
                "revised above, and were NOT re-run in this single pass — they may now be "
                "inconsistent with the revised canonical truth:",
                "",
                *[f"- {s}" for s in self.stale_sections],
                "",
                "This is the stale-layers problem: a single revision pass edits canonical truth "
                "in place but does not propagate it. Converging the downstream layers is the next step.",
            ]
        else:
            lines += [
                "### Potentially stale layers",
                "",
                "None — only final-layer section(s) were revised, so nothing downstream depends on them.",
            ]
        return "\n".join(lines)

    def write_artifacts(self) -> None:
        """Write the canonical bible + story as markdown and HTML reading copies."""
        self.logger.write_artifact("bible.md", self.bible.render())
        self.logger.write_artifact("story.md", self.bible.get("prose"))
        self.logger.write_html("story.html", "The Story", self.bible.get("prose"))
        self.logger.write_html("bible.html", "Story Bible", self.bible.render())
        # The judge report is a separate artifact — never folded into bible.md.
        if self.findings is not None:
            report = render_report(self.findings)
            self.logger.write_artifact("judge_report.md", report)
            self.logger.write_html("judge_report.html", "Consistency Report", report)
        # Revision artifacts (only when a revision pass ran).
        if self.revised_sections:
            self.logger.write_artifact("revision_report.md", self._revision_report())
            self.logger.write_html("revision_report.html", "Revision Report", self._revision_report())
        if self.findings_after is not None:
            after = render_report(self.findings_after)
            self.logger.write_artifact("judge_report_after.md", after)
            self.logger.write_html("judge_report_after.html", "Consistency Report (after revision)", after)

    # -- the whole run --------------------------------------------------------

    def run(self, raw_premise: str | None) -> StoryBible:
        """Premise -> full pipeline -> artifacts. Returns the finished bible.

        Pass raw_premise=None to have the editor generate the premise itself.
        """
        self.establish_premise(raw_premise)
        self.run_pipeline()
        self.run_judge()
        self.run_revision()
        self.write_artifacts()
        self.log(f"done -> {self.logger.dir}")
        return self.bible
