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


# Used by --generate-premise: the editor invents the one-line seed itself, which
# then flows through the same framing path as a user-supplied premise.
GENERATE_SYSTEM = """You are the Editor-in-Chief of a team that writes fantasy short stories. \
Invent ONE original, evocative one-sentence premise for a fantasy short story — the kind that implies a \
world, a tension, and a character's impossible problem in a single line. Favor the fresh and specific over \
genre clichés: no chosen ones, dark lords, ancient prophecies, or "last of their kind." Output only the \
single sentence, with no preamble, label, or quotation marks."""

GENERATE_TASK = "Invent the premise."
