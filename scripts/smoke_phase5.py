"""Phase 5 smoke test (throwaway) — judge reliability on KNOWN contradictions.

Builds a small bible with deliberately planted contradictions and runs ONLY the
consistency judge on it. This directly answers the question the advisory judge
exists to probe: can a single judge reliably catch inconsistencies? Cheaper and
far more diagnostic than judging a (hopefully consistent) freshly generated story.

Planted contradictions (what the judge SHOULD catch):
  1. Magic cost: magic section says casting costs BLOOD; the prose says it cost
     a MEMORY and no blood at all.
  2. Destroyed object reused: the blade Dawnedge is shattered "beyond any
     mending" in the plot, then drawn intact in the prose finale.
  3. Broken hard rule: magic says no one under sixteen can channel; the prose
     has a ten-year-old cast a spell.
  4. Death undone: the plot kills Coren; the prose has him speak afterward with
     no resurrection mechanism.

Run:  python scripts/smoke_phase5.py
"""

from dotenv import load_dotenv

from slopcannon.agents import ConsistencyJudge, render_report
from slopcannon.bible import StoryBible
from slopcannon.client import ModelClient
from slopcannon.runlog import RunLogger

PREMISE = "A border witch must spend herself to hold back a tide of glass."

WORLD = "The march-town of Sill sits on the Glass Coast. Its people fear the tide and trust their witches."

MAGIC = (
    "Casting is called **spending**. Every spell costs the caster their own **blood** — a witch opens a "
    "vein and the working drinks it; a large spell can drain a witch to fainting. There is no other price. "
    "**No one under the age of sixteen can channel**; the gift does not wake until then."
)

CHARACTERS = (
    "**Yarrow** — the border witch of Sill, in her forties, scarred along both forearms from a life of "
    "spending. **Coren** — her apprentice, nineteen. **Pip** — a ten-year-old who runs messages."
)

PLOT = (
    "1. The glass tide rises early; Yarrow rallies the town.\n"
    "2. Coren is killed when a glass wave breaks the seawall.\n"
    "3. Yarrow's blade **Dawnedge** is shattered beyond any mending against the tide-front.\n"
    "4. Yarrow makes a final stand and spends the last of herself to turn the tide.\n"
)

# The prose deliberately contradicts the above in four places.
PROSE = (
    "Yarrow raised her hand and spent the spell. It cost her a memory — her mother's face, gone in a warm "
    "rush — and not a drop of blood; her sleeves stayed dry. The ward bloomed gold over the seawall.\n\n"
    "Beside her, Pip, all of ten years old, set her small jaw and cast a second ward of her own, the light "
    "leaping eager from her fingers.\n\n"
    "\"Hold the line!\" Coren shouted, very much alive, hauling a child from the surf and grinning back at "
    "Yarrow as though the seawall had never touched him.\n\n"
    "When the tide-front came, Yarrow drew **Dawnedge** — whole, bright, unbroken — and the blade sang as it "
    "clove the wave of glass in two."
)


def main() -> None:
    load_dotenv()

    logger = RunLogger()
    print(f"run dir: {logger.dir}\n")

    bible = StoryBible()
    bible.set("premise", PREMISE)
    bible.set("world", WORLD)
    bible.set("magic", MAGIC)
    bible.set("characters", CHARACTERS)
    bible.set("plot", PLOT)
    bible.set("prose", PROSE)

    client = ModelClient(logger)
    judge = ConsistencyJudge()

    print(f"running judge ({judge.config.model}) over a bible with 4 planted contradictions ...\n")
    findings = judge.run(bible, client)
    report = render_report(findings)

    logger.write_artifact("judge_report.md", report)
    logger.write_html("judge_report.html", "Consistency Report", report)

    print(report)
    print("\n--- structured routing targets (most-downstream section per finding) ---")
    order = ["premise", "world", "magic", "characters", "plot", "prose"]
    for f in findings:
        target = max(f.sections, key=order.index) if f.sections else "?"
        print(f"  [{f.severity}] sections={f.sections} -> target={target}")
    print(f"\nreport + trace under: {logger.dir}")


if __name__ == "__main__":
    main()
