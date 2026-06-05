"""Phase 6 smoke test (throwaway) — live demo of the single revision pass.

We INJECT the findings rather than rely on the judge to detect them, so the
stale-layers path runs deterministically (the judge's detection reliability is a
separate question — it tends to catch concrete continuity clashes but miss
inference-based ones). The revision, in-place commit, history archival, stale-layer
detection, and re-judge are all real model/disk operations.

Planted bible + injected findings:
  - world vs magic: city runs on SUNLIGHT (weak at night) vs wardcraft drawn from
    the MOON (strongest at night). Target = magic (downstream) -> magic revised in
    place -> characters & plot (built on moon-magic) go STALE.
  - plot vs prose: the Sunbridge collapses in the plot but is crossed intact in the
    prose. Target = prose -> revised, no staleness (it's the last layer).

Run:  python scripts/smoke_phase6.py
"""

from dotenv import load_dotenv

from slopcannon.agents import Finding
from slopcannon.client import ModelClient
from slopcannon.orchestrator import EditorInChief
from slopcannon.runlog import RunLogger

BIBLE = {
    "premise": "A warden defends a sunlit city from a creeping dark.",
    "world": (
        "The city of **Vant** runs on **sunlight**: every ward and lamp draws on daylight stored in glass "
        "cells across the rooftops. The city is strongest at noon and **weakest after dark**."
    ),
    "magic": (
        "Wardcraft draws its power from **the moon**. A warden's workings are **strongest at night** under a "
        "full moon and **fail completely in daylight**."
    ),
    "characters": (
        "**Sel** is Vant's night-warden. She works only after dark, when her moon-drawn craft is at its "
        "height, and sleeps through the daylight hours."
    ),
    "plot": (
        "1. The dark creeps in; Sel raises her strongest wards at midnight by the full moon.\n"
        "2. The **Sunbridge** collapses into the river as the dark undermines it.\n"
        "3. Sel makes her stand at the broken span and turns back the dark before dawn.\n"
    ),
    "prose": (
        "By moonlight Sel walked out to meet the dark, her wards burning silver at the full moon's height. "
        "She crossed the **Sunbridge** at a run, its stone span whole and steady beneath her boots."
    ),
}

INJECTED_FINDINGS = [
    Finding(
        severity="high",
        sections=["world", "magic"],
        summary="Magic's power source contradicts the world's.",
        quote_a="The city of Vant runs on sunlight ... weakest after dark",
        quote_b="Wardcraft draws its power from the moon ... strongest at night",
        why="The world's power is sunlight and it is weakest at night; the magic is moon-drawn and strongest at night.",
    ),
    Finding(
        severity="high",
        sections=["plot", "prose"],
        summary="The Sunbridge is collapsed in the plot but crossed intact in the prose.",
        quote_a="The Sunbridge collapses into the river",
        quote_b="She crossed the Sunbridge at a run, its stone span whole and steady",
        why="The plot destroys the bridge; the prose crosses it intact.",
    ),
]


def main() -> None:
    load_dotenv()
    logger = RunLogger()
    print(f"run dir: {logger.dir}\n")

    client = ModelClient(logger)
    editor = EditorInChief(client, logger, judge=True, revise=True, log=print)

    for section, text in BIBLE.items():
        editor.commit(section, text)

    # Inject findings to exercise the revision machinery deterministically.
    editor.findings = INJECTED_FINDINGS
    editor.run_revision()
    editor.write_artifacts()

    print("\n=== revised in place ===", editor.revised_sections)
    print("=== stale layers     ===", editor.stale_sections)
    print("=== findings after re-judge ===", len(editor.findings_after or []))
    print(f"\nartifacts under: {logger.dir}")
    print("  - revision_report.md   (what changed + stale layers)")
    print("  - revisions/*.superseded.md  (archived old versions)")


if __name__ == "__main__":
    main()
