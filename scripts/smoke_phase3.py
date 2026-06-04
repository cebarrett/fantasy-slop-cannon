"""Phase 3 smoke test (throwaway).

Runs the full worker chain by hand — worldbuilder -> magic -> character -> plot
-> prose — committing each section as we go, then writes the bible and the story.
This is the pipeline minus the editor-in-chief (Phase 4) and the judge (Phase 5).

Checkpoint goal: a complete bible + a full story come out the far end.

Run from the repo root:  python scripts/smoke_phase3.py
"""

from dotenv import load_dotenv

from slopcannon.agents import PIPELINE
from slopcannon.bible import StoryBible
from slopcannon.client import ModelClient
from slopcannon.runlog import RunLogger

PREMISE = (
    "In a desert city where memories can be traded like currency, a debt collector "
    "discovers the ledger she enforces is built on a stolen memory of her own."
)


def main() -> None:
    load_dotenv()

    logger = RunLogger()
    print(f"run dir: {logger.dir}\n")

    bible = StoryBible()
    bible.set("premise", PREMISE)

    client = ModelClient(logger)

    for AgentClass in PIPELINE:
        agent = AgentClass()
        print(f"running {agent.name} ({agent.config.model}) -> section '{agent.section}' ...")
        contribution = agent.run(bible, client)
        bible.set(agent.section, contribution)  # editor-in-chief commits
        print(f"  committed {len(contribution)} chars")

    logger.write_artifact("bible.md", bible.render())
    logger.write_artifact("story.md", bible.get("prose"))
    logger.write_html("story.html", "The Story", bible.get("prose"))
    logger.write_html("bible.html", "Story Bible", bible.render())

    print(f"\ndone. bible + story (md + html) + traces under: {logger.dir}")


if __name__ == "__main__":
    main()
