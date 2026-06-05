"""Tests for the editor gating the optional magic stage.

Deterministic: a fake client returns canned text so run_pipeline executes without
network. Verifies that include_magic controls whether the magic section exists,
and that skipping it does not skip the other stages.
"""

from slopcannon.client import CallResult
from slopcannon.orchestrator import EditorInChief
from slopcannon.runlog import RunLogger


class FakeClient:
    """Records which agents ran and returns canned output."""

    def __init__(self):
        self.ran: list[str] = []

    def call(self, config, *, system, user):
        self.ran.append(config.name)
        return CallResult(
            text=f"{config.name} content",
            input_tokens=1,
            output_tokens=1,
            stop_reason="end_turn",
            latency_ms=1,
        )


def make_editor(tmp_path):
    return EditorInChief(FakeClient(), RunLogger(root=tmp_path, run_id="t"), judge=False)


def test_magic_stage_runs_by_default(tmp_path):
    e = make_editor(tmp_path)
    e.commit("premise", "a premise")
    e.include_magic = True
    e.run_pipeline()
    assert e.bible.has("magic")
    assert e.client.ran == ["worldbuilder", "magic", "character", "plot", "prose"]


def test_magic_stage_skipped_when_editor_opts_out(tmp_path):
    e = make_editor(tmp_path)
    e.commit("premise", "a strictly mundane premise")
    e.include_magic = False
    e.run_pipeline()

    # No magic section, and the magic agent never ran...
    assert not e.bible.has("magic")
    assert "magic" not in e.client.ran
    # ...but every other stage still did.
    assert e.client.ran == ["worldbuilder", "character", "plot", "prose"]
    for section in ["world", "characters", "plot", "prose"]:
        assert e.bible.has(section)
