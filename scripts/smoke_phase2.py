"""Phase 2 smoke test (throwaway).

Seeds a hardcoded premise into the bible (premise expansion / the editor arrive
in Phase 4), runs the real Worldbuilder live, commits its output, and writes the
bible. Checkpoint goal: one real section, fully logged.

Run from the repo root:  python scripts/smoke_phase2.py
"""

from dotenv import load_dotenv

from slopcannon.agents import Worldbuilder
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
    print(f"run dir: {logger.dir}")

    bible = StoryBible()
    bible.set("premise", PREMISE)

    client = ModelClient(logger)
    worldbuilder = Worldbuilder()

    contribution = worldbuilder.run(bible, client)
    bible.set(worldbuilder.section, contribution)  # editor-in-chief commits

    logger.write_artifact("bible.md", bible.render())

    print("\n--- world section ---")
    print(contribution)
    print(f"\nbible + traces under: {logger.dir}")


if __name__ == "__main__":
    main()
