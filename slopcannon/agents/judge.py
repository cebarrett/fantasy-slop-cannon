"""The Consistency Judge — an advisory reviewer, not a producer.

Unlike the worker agents, the judge reads the *full* bible (including the prose),
writes no section, and its output is never committed to canonical truth. So it
deliberately does NOT subclass Agent or reuse the worker collaboration rules.

It returns STRUCTURED findings (via a forced tool call) so the revision pass can
route each contradiction to the section that should change. The human-readable
report is rendered from those findings, so the report and the routing data never
drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..bible import SECTION_ORDER, StoryBible
from ..client import ModelClient
from ..config import AgentConfig, get_config
from ..prompts import judge as P

# Tool the judge is forced to call. Section keys are constrained to the canonical
# bible sections so findings are routable without parsing prose.
JUDGE_TOOL = {
    "name": "report_consistency",
    "description": "Report every consistency contradiction found in the bible and prose.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "description": "All contradictions found; empty if the story is consistent.",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                        "sections": {
                            "type": "array",
                            "items": {"type": "string", "enum": list(SECTION_ORDER)},
                            "description": "The bible sections in conflict (exact keys).",
                        },
                        "summary": {"type": "string", "description": "One-line description of the contradiction."},
                        "quote_a": {"type": "string", "description": "Short verbatim quote from one side."},
                        "quote_b": {"type": "string", "description": "Short verbatim quote from the other side."},
                        "why": {"type": "string", "description": "One sentence on why they conflict."},
                    },
                    "required": ["severity", "sections", "summary", "quote_a", "quote_b", "why"],
                },
            }
        },
        "required": ["findings"],
    },
}


@dataclass
class Finding:
    severity: str
    sections: list[str]
    summary: str
    quote_a: str
    quote_b: str
    why: str

    @classmethod
    def from_dict(cls, d: dict) -> "Finding":
        return cls(
            severity=d.get("severity", "low"),
            sections=[s for s in d.get("sections", []) if s in SECTION_ORDER],
            summary=d.get("summary", ""),
            quote_a=d.get("quote_a", ""),
            quote_b=d.get("quote_b", ""),
            why=d.get("why", ""),
        )


def render_report(findings: list[Finding]) -> str:
    """Render structured findings as a human-readable markdown report."""
    if not findings:
        return "## Consistency Report\n\nNo contradictions found."
    lines = ["## Consistency Report", ""]
    for f in findings:
        where = " vs ".join(f.sections) if f.sections else "unspecified"
        lines += [
            f"- **[severity: {f.severity}]** {f.summary}",
            f"  - where: {where}",
            f'  - quote A: "{f.quote_a}"',
            f'  - quote B: "{f.quote_b}"',
            f"  - why it conflicts: {f.why}",
        ]
    return "\n".join(lines)


class ConsistencyJudge:
    name = "judge"

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or get_config(self.name)

    def run(self, bible: StoryBible, client: ModelClient) -> list[Finding]:
        """Read the full bible + prose, return structured findings (advisory)."""
        data = client.call_structured(
            self.config,
            system=P.SYSTEM,
            user=P.task(bible.render()),
            tool=JUDGE_TOOL,
        )
        return [Finding.from_dict(d) for d in data.get("findings", [])]
