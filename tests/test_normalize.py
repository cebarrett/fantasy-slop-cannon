"""Tests for the editor's contribution normalization.

This is the heading-deduplication fix from the Phase 3 finding: workers emit a
leading heading naming their own section even though render() adds one. We strip
only that redundant heading — never genuine sub-headings or real story titles.
"""

from slopcannon.orchestrator import normalize_contribution


def test_strips_redundant_section_heading():
    text = "## Magic System\n\nMagic costs blood here."
    assert normalize_contribution("magic", text) == "Magic costs blood here."


def test_strips_heading_matching_section_key():
    text = "# world\n\nA city of salt."
    assert normalize_contribution("world", text) == "A city of salt."


def test_keeps_genuine_subheadings_after_stripping_top():
    text = "## Magic System\n\n### The Craft\n\nDetails."
    assert normalize_contribution("magic", text) == "### The Craft\n\nDetails."


def test_keeps_a_real_story_title_that_is_not_the_section_name():
    text = "## The Memory Ledger\n\nOnce, in the desert..."
    # 'The Memory Ledger' is not the prose section's name/title -> left intact.
    assert normalize_contribution("prose", text) == text.strip()


def test_noop_when_no_leading_heading():
    text = "Just prose, no heading."
    assert normalize_contribution("world", text) == text


def test_strips_leading_blank_lines_before_heading():
    text = "\n\n## Characters\n\nSenne, a debt collector."
    assert normalize_contribution("characters", text) == "Senne, a debt collector."
