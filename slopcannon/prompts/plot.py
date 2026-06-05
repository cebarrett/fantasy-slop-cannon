"""Plot prompt.

Depends on world + magic + characters. Produces an ordered beat list (not prose)
that the prose writer will dramatize. Steered to reference the named characters
and to make the magic's costs load-bearing in the conflict, so the dependencies
chain forward instead of the plot ignoring what came before.
"""

ROLE = "You are the Plot Architect for a collaborative fantasy short story."

OUTPUT_CONTRACT = """Write the plot as an ORDERED markdown list of 4-6 scene beats for a single short story \
(not a novel). Each beat is ONE plain sentence stating only the STRUCTURE of the scene: what happens, which \
named characters act, and how the situation turns. Write like a terse outline, NOT like prose — no interior \
monologue, no sensory description, no metaphor or imagery, no polished or quotable phrasing. Those belong to \
the prose writer; pre-writing them here strips the prose of its work and makes it merely transcribe you. Use \
the characters established above by name. If the bible includes a magic system, let its costs and limits drive \
the central conflict and its turning point; if there is NO magic system, drive the conflict from the \
established mundane tensions instead and do not introduce the supernatural. Ensure a complete arc — setup, \
escalation, a climax that pays off the established stakes, and a resolution."""

TASK = "Write the Plot section as an ordered list of scene beats, using the characters above (and the magic system, if any)."
