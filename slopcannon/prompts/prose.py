"""Prose prompt.

The integration call: turns the plot beats into the actual short story while
honoring every prior section. Single call (no scene-by-scene fan-out in the MVP).
Length-bounded so it stays a short story and doesn't blow the token ceiling.
This is the agent most likely to quietly introduce inconsistencies, which is
exactly what the judge exists to catch.
"""

ROLE = "You are the Prose Writer for a collaborative fantasy short story."

OUTPUT_CONTRACT = """Write the complete short story in markdown: roughly 1800-3000 words. Dramatize the plot \
beats above in order, in actual scenes with prose and dialogue — show, don't summarize. Stay faithful to the \
world and the characters as established, and — if the bible defines a magic system — its costs and limits; \
do not contradict any locked detail, and do not invent magic (or, if the world has none, introduce the \
supernatural at all). Use a blank line or a simple scene break between scenes. Write only the story itself — \
no title card, no author's note, no recap of the bible."""

TASK = "Write the full Story, dramatizing the plot beats above and honoring every section of the bible."
