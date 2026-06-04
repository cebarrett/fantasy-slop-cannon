# fantasy-slop-cannon

A hierarchical multi-agent system that writes a fantasy short story. It's a
**learning project**: the point is the orchestration — agent hierarchy,
sequential dependencies, a producer/judge split, and a single shared "truth" that
agents contribute to — not the fiction. The story is just the vehicle.

A thin **editor-in-chief** sequences a pipeline of specialist agents. Each one
reads the story-so-far and adds its piece; a consistency **judge** reviews the
result at the end. Every model call's full input and output is logged to disk so
you can see exactly which agent introduced what.

## How it works

```
editor-in-chief  (generates/expands the premise, sequences the run, commits each
       │          contribution to the bible, runs the judge)
       ▼
   premise ─▶ world ─▶ magic ─▶ characters ─▶ plot ─▶ prose ─▶ [ judge ]
            worldbuilder  magic   character    plot   prose    consistency
                          system   designer  architect writer    judge
```

- **Sequential pipeline, one forward pass.** Each stage runs once and reads
  everything the previous stages committed. World and magic come first and
  constrain everything after them; the prose writer dramatizes the locked plot.
- **The "story bible" is the shared state** — a small set of markdown sections
  (`premise`, `world`, `magic`, `characters`, `plot`, `prose`), one author each.
  It all fits comfortably in context, so there's no retrieval/RAG machinery.
- **One commit seam.** Every contribution becomes canonical truth through a
  single method on the editor, which normalizes it before writing. That's the one
  place "the current truth" is updated.
- **The judge is advisory.** It reads the finished bible + story and prints the
  contradictions it finds (broken magic costs, continuity errors, etc.). It never
  edits the bible, blocks the run, or triggers a rewrite.
- **Everything is logged.** Each run gets its own timestamped directory with the
  exact input/output of every model call.

Models are configurable per agent (defaults: Opus for the editor, prose writer,
and judge; Sonnet for the other workers).

## Setup

Requires Python 3.11+ and an Anthropic API key.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

cp .env.example .env        # then put your key in .env:
#   ANTHROPIC_API_KEY=sk-ant-...
```

## Generate a story

```bash
# Use the default premise:
python cli.py

# Supply your own one-line premise:
python cli.py --premise "A lighthouse keeper learns the light is not warning
ships away but holding something vast and sleeping beneath the waves."

# Let the editor invent a premise:
python cli.py --generate-premise
```

Useful flags:

| Flag | Effect |
|------|--------|
| `--premise "..."` | Supply the one-line premise (default if none given) |
| `--generate-premise` | Have the editor invent the premise instead |
| `--no-expand-premise` | Commit the raw premise instead of expanding it into a brief |
| `--no-judge` | Skip the advisory consistency judge |
| `--model AGENT=MODEL` | Override an agent's model, repeatable (e.g. `--model prose=claude-sonnet-4-6`) |
| `--runs-dir DIR` | Where to write run output (default `runs/`) |

## Output

Each run writes a timestamped directory under `runs/`:

```
runs/2026-06-04T17-47-37Z/
  00_editor.input.md   00_editor.output.md     # exact input + output per call,
  01_worldbuilder...   ...                      #   numbered in execution order
  06_judge.input.md    06_judge.output.md
  run.jsonl            # one event per call: model, tokens, latency, stop reason
  bible.md             # the full canonical bible
  story.md             # just the prose
  story.html           # dark-theme reading copy (open in a browser)
  bible.html
  judge_report.md      # the judge's findings (also .html)
```

## Layout

```
slopcannon/            # importable library — all orchestration logic
  config.py            # per-agent model configuration
  bible.py             # StoryBible: the shared markdown state
  client.py            # raw Anthropic SDK wrapper; every call is logged here
  runlog.py            # per-run logging + artifact writing
  html.py              # markdown -> dark-theme HTML
  orchestrator.py      # EditorInChief: sequences the run, owns the commit seam
  agents/              # the worker agents and the judge
  prompts/             # one prompt module per agent
cli.py                 # thin entry point
tests/                 # unit tests
scripts/               # throwaway per-phase smoke tests
```

The library is import-only (no argv/stdout); `cli.py` is the entry point.
```python
from slopcannon.orchestrator import EditorInChief   # drive a run programmatically
```
