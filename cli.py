"""Thin CLI entry point for the slopcannon story pipeline.

All orchestration lives in the importable `slopcannon` package; this file just
parses args, loads .env, wires a run together, and prints progress. Run it as:

    python cli.py
    python cli.py --premise "your one-line premise"
    python cli.py --no-expand-premise
    python cli.py --model prose=claude-sonnet-4-6 --model judge=claude-opus-4-8
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

from slopcannon.client import ModelClient
from slopcannon.config import DEFAULTS, get_config
from slopcannon.orchestrator import EditorInChief
from slopcannon.runlog import RunLogger

DEFAULT_PREMISE = (
    "In a desert city where memories can be traded like currency, a debt collector "
    "discovers the ledger she enforces is built on a stolen memory of her own."
)


def build_overrides(items: list[str]) -> dict[str, "object"]:
    """Parse --model AGENT=MODEL pairs into per-agent config overrides."""
    overrides: dict[str, object] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--model expects AGENT=MODEL, got: {item!r}")
        name, model = item.split("=", 1)
        name, model = name.strip(), model.strip()
        if name not in DEFAULTS:
            raise SystemExit(
                f"unknown agent {name!r}. Known: {', '.join(DEFAULTS)}"
            )
        overrides[name] = get_config(name).with_overrides(model=model)
    return overrides


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a fantasy short story with a multi-agent pipeline.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--premise", default=DEFAULT_PREMISE, help="one-line story premise")
    source.add_argument(
        "--generate-premise",
        action="store_true",
        help="have the editor invent the premise instead of supplying one",
    )
    parser.add_argument(
        "--no-expand-premise",
        action="store_true",
        help="commit the raw premise instead of having the editor expand it",
    )
    parser.add_argument(
        "--no-judge",
        action="store_true",
        help="skip the advisory consistency judge at the end",
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        metavar="AGENT=MODEL",
        help="override an agent's model (repeatable), e.g. --model prose=claude-sonnet-4-6",
    )
    parser.add_argument("--runs-dir", default="runs", help="where to write run output")
    args = parser.parse_args()

    load_dotenv()  # entry point's job: pull ANTHROPIC_API_KEY into the env

    logger = RunLogger(root=args.runs_dir)
    print(f"run dir: {logger.dir}\n")

    client = ModelClient(logger)
    editor = EditorInChief(
        client,
        logger,
        expand_premise=not args.no_expand_premise,
        judge=not args.no_judge,
        agent_configs=build_overrides(args.model),
        log=print,
    )

    # None signals the editor to invent the premise itself.
    editor.run(None if args.generate_premise else args.premise)

    print(f"\nRead the story:  {logger.dir / 'story.html'}")
    print(f"Read the bible:  {logger.dir / 'bible.html'}")
    if editor.judge_findings is not None:
        print(f"Consistency:     {logger.dir / 'judge_report.html'}")


if __name__ == "__main__":
    main()
