"""Editor-in-Chief prompt.

The editor is the orchestrator, not a worker. In the MVP its premise call does two
coordinator jobs at once, returned via the frame_premise tool:

  1. Frame the raw premise into a short brief (preserving everything the user
     specified, inventing nothing they didn't).
  2. Decide which OPTIONAL specialist stages this story actually needs — currently
     just: does it need a magic/supernatural system? This is what stops the magic
     agent from forcing magic into a premise that explicitly excludes it. The
     decision is a scoping call, which is the coordinator's job, not the magic
     specialist's (whose role primes it to always invent one).
"""

SYSTEM = """You are the Editor-in-Chief of a small team writing a single fantasy short story. You do not \
write the world, magic, characters, plot, or prose yourself — specialist agents do that. Turn the raw \
premise into a short brief AND decide which optional specialist stages the story needs, reporting both via \
the frame_premise tool.

THE BRIEF (3-5 sentences): frame the work — the hook, the intended tone, and the central tension the finished \
story should deliver. Anything the premise specifies is a REQUIREMENT, not a suggestion: a named setting, \
named characters, an author or style to emulate, a genre, or any other explicit instruction. Preserve every \
such detail in the brief, by name and unchanged — never drop it, rename it, or genericize it. Do NOT invent \
NEW specifics (place names, magic rules, character names, plot beats) the premise did not ask for; leave \
whatever it left open for the specialists.

THE MAGIC DECISION (include_magic): does this story need a magic or supernatural system? Default to true for \
most fantasy. Set it to FALSE when the premise calls for a grounded, mundane, historical, or strictly \
low/no-magic story, or when it explicitly excludes magic or the supernatural. When false, no magic system \
will be created and no other agent will add one — so respect the premise and do not smuggle the supernatural \
back in through the brief."""


def premise_task(raw_premise: str) -> str:
    return f"Raw premise:\n\n{raw_premise}\n\nFrame it and decide the magic stage via the frame_premise tool."


# Tool the editor is forced to call for premise framing + stage scoping.
EDITOR_TOOL = {
    "name": "frame_premise",
    "description": "Provide the framing brief and decide which optional specialist stages the story needs.",
    "input_schema": {
        "type": "object",
        "properties": {
            "brief": {"type": "string", "description": "The 3-5 sentence framing brief."},
            "include_magic": {
                "type": "boolean",
                "description": "Whether this story needs a magic/supernatural system.",
            },
            "magic_reason": {
                "type": "string",
                "description": "One short sentence justifying the include_magic decision.",
            },
        },
        "required": ["brief", "include_magic", "magic_reason"],
    },
}


# ---------------------------------------------------------------------------
# Premise generation — used by --generate-premise
# ---------------------------------------------------------------------------
# The generator was collapsing into one attractor: solitary bereaved woman +
# memory-as-substance + water + quiet internal tragedy. Good clichés were
# banned, but "evocative + specific + impossible personal problem" is itself a
# narrow target the model satisfies the same way every time.
#
# Fix: inject a per-run diversity seed drawn randomly by the orchestrator.
# The seed specifies tone, the emotional core, structural shape, and two
# concrete nouns. It's a constraint, not a template — it nudges each
# independent draw off the attractor without prescribing the premise.

import random

# Vocabularies for the diversity seed. Intentionally broad and mutually
# covering across axes — the goal is to make the full space reachable, not
# to guarantee any specific premise.
_TONES = [
    "dry comedy", "absurdist farce", "wonder and awe", "horror",
    "political thriller", "heist", "pastoral", "swashbuckling adventure",
    "dark comedy", "mystery", "coming-of-age", "revenge tragedy",
    "warm satire", "cosmic dread",
]

_EMOTIONAL_CORES = [
    "ambition", "envy", "obsession", "righteous rage", "shame",
    "curiosity", "joy", "fear of the wrong thing", "pride",
    "desperate hope", "boredom", "loyalty", "jealousy",
    "wonder", "competitiveness", "guilt that turns out to be wrong",
]

_STRUCTURES = [
    "a heist that goes wrong in an unexpected way",
    "a chase or pursuit",
    "a negotiation or bargain between mismatched parties",
    "a competition with an absurd or impossible judging criterion",
    "an unmasking — someone is not who they appear",
    "a transformation the protagonist resists",
    "an escape from an institution or system",
    "a first meeting between two people who should be enemies",
    "a delivery or errand that keeps going wrong",
    "an audit or investigation that uncovers the wrong thing",
]

_NOUNS = [
    "lighthouse", "tax ledger", "glacier", "printing press", "salt mine",
    "observatory", "granary", "shipyard", "clock tower", "census roll",
    "plague hospital", "dam", "postal route", "quarry", "weather station",
    "bridge toll", "cartographer's guild", "patent office", "harbor pilot",
    "city gate", "debtor's prison", "census taker", "market inspector",
    "guild exam", "messenger pigeon", "border checkpoint", "irrigation canal",
]


def draw_seed(rng: random.Random | None = None) -> dict:
    """Draw one random diversity seed. Pass an seeded rng for reproducibility."""
    r = rng or random
    nouns = r.sample(_NOUNS, 2)
    return {
        "tone": r.choice(_TONES),
        "emotional_core": r.choice(_EMOTIONAL_CORES),
        "structure": r.choice(_STRUCTURES),
        "objects": nouns,
    }


def seed_note(seed: dict) -> str:
    return (
        f"tone={seed['tone']}, emotional_core={seed['emotional_core']}, "
        f"structure={seed['structure']}, objects=[{', '.join(seed['objects'])}]"
    )


GENERATE_SYSTEM = """You are the Editor-in-Chief of a team that writes fantasy short stories. \
Invent ONE original, evocative one-sentence premise for a fantasy short story — the kind that implies a \
world, a tension, and a character's impossible problem in a single line. Favor the fresh and specific over \
genre clichés: no chosen ones, dark lords, ancient prophecies, or "last of their kind." Not every story is a \
quiet tragedy; vary tone and genre freely. Output only the single sentence, with no preamble, label, or \
quotation marks."""


def generate_task(seed: dict) -> str:
    """The user message for premise generation, including the diversity seed."""
    return (
        f"Diversity seed for this premise: {seed_note(seed)}\n\n"
        "Let the seed push you toward a premise you wouldn't reach without it — "
        "it's a constraint to build from, not a template to fill in. "
        "The objects don't have to appear literally; they can suggest a setting, "
        "an economy, a profession, or a conflict. Invent the premise."
    )
