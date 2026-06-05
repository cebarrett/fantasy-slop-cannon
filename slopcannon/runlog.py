"""Run logging — the part we build first and never let slip.

Every model call's *exact* system + user input and full output is written to a
per-run directory so that when the story comes out weird you can read precisely
which agent introduced the weirdness and what it was reacting to. This is the
same instinct as saving eval traces: cheap now, painful to retrofit.

Logging is wired through the model client (see client.py) so it is structurally
impossible to make a call that isn't logged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CallRecord:
    """Everything we know about one model call, for the jsonl event log."""

    index: int
    agent: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    stop_reason: str | None


class RunLogger:
    """Owns one run's output directory and writes per-call traces + artifacts."""

    def __init__(self, root: str | Path = "runs", run_id: str | None = None) -> None:
        if run_id is None:
            # UTC, filesystem-safe. One directory per run.
            run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        self.run_id = run_id
        self.dir = Path(root) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self._events_path = self.dir / "run.jsonl"

    # -- per-call tracing -----------------------------------------------------

    def log_call(
        self,
        *,
        index: int,
        agent: str,
        model: str,
        system: str,
        user: str,
        output: str,
        input_tokens: int | None,
        output_tokens: int | None,
        latency_ms: int,
        stop_reason: str | None,
    ) -> None:
        """Write the input trace, the output trace, and one jsonl event."""
        stem = f"{index:02d}_{agent}"

        input_md = (
            f"# {agent} — input (call {index:02d})\n\n"
            f"- model: `{model}`\n\n"
            f"## system\n\n{system}\n\n"
            f"## user\n\n{user}\n"
        )
        (self.dir / f"{stem}.input.md").write_text(input_md, encoding="utf-8")

        output_md = (
            f"# {agent} — output (call {index:02d})\n\n"
            f"- model: `{model}`\n"
            f"- stop_reason: `{stop_reason}`\n"
            f"- tokens: in={input_tokens} out={output_tokens}\n"
            f"- latency_ms: {latency_ms}\n\n"
            f"---\n\n{output}\n"
        )
        (self.dir / f"{stem}.output.md").write_text(output_md, encoding="utf-8")

        record = CallRecord(
            index=index,
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            stop_reason=stop_reason,
        )
        event = {"ts": datetime.now(timezone.utc).isoformat(), **record.__dict__}
        with self._events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    # -- final artifacts ------------------------------------------------------

    def write_artifact(self, filename: str, content: str) -> Path:
        """Write a top-level artifact (bible.md, story.md, judge_report.md)."""
        path = self.dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def archive_revision(self, section: str, old_text: str) -> Path:
        """Archive a superseded section to logs before it's overwritten in place.

        This is the canonicalization discipline: the bible holds only the current
        truth, while the version history lives here in the run log — never inline
        where a later agent might read a stale version.
        """
        rdir = self.dir / "revisions"
        rdir.mkdir(exist_ok=True)
        path = rdir / f"{section}.superseded.md"
        path.write_text(old_text, encoding="utf-8")
        return path

    def write_html(self, filename: str, title: str, markdown_text: str) -> Path:
        """Write a dark-theme HTML reading copy of some markdown (story/bible)."""
        from .html import render_page

        path = self.dir / filename
        path.write_text(render_page(title, markdown_text), encoding="utf-8")
        return path
