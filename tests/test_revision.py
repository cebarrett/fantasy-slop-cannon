"""Tests for the revision pass's pure logic — routing, staleness, in-place edits.

These are deterministic and need no model calls: they verify the canonicalization
machinery itself, separately from the judge's (model-dependent) detection.
"""

from slopcannon.agents import Finding
from slopcannon.orchestrator import EditorInChief
from slopcannon.runlog import RunLogger


def make_editor(tmp_path):
    return EditorInChief(None, RunLogger(root=tmp_path, run_id="t"))


def finding(severity, sections):
    return Finding(severity, list(sections), "summary", "A", "B", "why")


# -- routing (foundational-first: target = most-downstream section) -----------

def test_target_is_most_downstream_section(tmp_path):
    e = make_editor(tmp_path)
    groups = e._targets([finding("high", ["magic", "prose"])])
    assert list(groups) == ["prose"]


def test_mid_layer_target_when_two_bible_sections_conflict(tmp_path):
    e = make_editor(tmp_path)
    groups = e._targets([finding("high", ["world", "magic"])])
    assert list(groups) == ["magic"]


def test_low_severity_and_premise_only_are_skipped(tmp_path):
    e = make_editor(tmp_path)
    findings = [finding("low", ["magic", "prose"]), finding("high", ["premise"])]
    assert e._targets(findings) == {}


# -- stale-layer detection ----------------------------------------------------

def populated_editor(tmp_path):
    e = make_editor(tmp_path)
    for s in ["premise", "world", "magic", "characters", "plot", "prose"]:
        e.bible.set(s, f"{s} text")
    return e


def test_revising_mid_layer_makes_everything_after_it_stale(tmp_path):
    e = populated_editor(tmp_path)
    e.revised_sections = ["magic"]
    assert e._stale_layers() == ["characters", "plot", "prose"]


def test_revised_downstream_sections_are_not_stale(tmp_path):
    e = populated_editor(tmp_path)
    e.revised_sections = ["magic", "prose"]
    assert e._stale_layers() == ["characters", "plot"]


def test_revising_only_the_last_layer_leaves_nothing_stale(tmp_path):
    e = populated_editor(tmp_path)
    e.revised_sections = ["prose"]
    assert e._stale_layers() == []


# -- in-place edit with history to logs ---------------------------------------

def test_revise_section_overwrites_in_place_and_archives_history(tmp_path):
    e = make_editor(tmp_path)
    e.bible.set("magic", "OLD magic rules")

    e.revise_section("magic", "NEW magic rules")

    # Canonical truth updated in place...
    assert e.bible.get("magic") == "NEW magic rules"
    assert e.revised_sections == ["magic"]
    # ...the superseded version lives in the logs, not the bible...
    superseded = e.logger.dir / "revisions" / "magic.superseded.md"
    assert superseded.exists()
    assert "OLD magic rules" in superseded.read_text()
    # ...and the rendered bible shows only the current truth.
    rendered = e.bible.render()
    assert "NEW magic rules" in rendered
    assert "OLD magic rules" not in rendered
