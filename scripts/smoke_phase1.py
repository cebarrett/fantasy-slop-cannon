"""Phase 1 smoke test (throwaway).

Proves the skeleton end-to-end: .env loads, the Anthropic SDK works, one model
call is made through ModelClient, and a full trace lands on disk in a fresh run
directory. Also exercises the StoryBible round-trip so we know it renders.

Run from the repo root:  python scripts/smoke_phase1.py
"""

from dotenv import load_dotenv

from slopcannon.bible import StoryBible
from slopcannon.client import ModelClient
from slopcannon.config import get_config
from slopcannon.runlog import RunLogger


def main() -> None:
    load_dotenv()  # entry point's job: pull ANTHROPIC_API_KEY into the env

    logger = RunLogger()
    print(f"run dir: {logger.dir}")

    client = ModelClient(logger)
    result = client.call(
        get_config("worldbuilder"),
        system="You are a fantasy bard. Be vivid and brief.",
        user="In one sentence, greet a traveler arriving at a city gate at dusk.",
    )

    print("\n--- model said ---")
    print(result.text)
    print("------------------")
    print(
        f"tokens in/out: {result.input_tokens}/{result.output_tokens}  "
        f"stop={result.stop_reason}  latency={result.latency_ms}ms"
    )

    # Exercise the bible round-trip and drop it as an artifact.
    bible = StoryBible()
    bible.set("premise", "A throwaway smoke-test premise.")
    bible.set("world", result.text)
    logger.write_artifact("bible.md", bible.render())

    print(f"\ntraces + bible.md written under: {logger.dir}")


if __name__ == "__main__":
    main()
