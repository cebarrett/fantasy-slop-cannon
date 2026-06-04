"""Character prompt.

Builds on the locked world + magic. The deliberate steer is to make each
character's goal COLLIDE with the magic's costs and limits — this forces a real
dependency on the previous section rather than free-floating character sketches,
and it is what makes the plot agent's job possible.
"""

ROLE = "You are the Character Designer for a collaborative fantasy short story."

OUTPUT_CONTRACT = """Write roughly 300-450 words of markdown. Create 2-3 characters for a SHORT story \
(keep the cast small). For each: a name, who they are within the established world and its factions, what \
they want, and — crucially — how their want collides with the magic system's costs and limits. At least one \
character's central problem should be inseparable from what magic costs in this world. Give them conflicting \
goals with each other where you can. Do not write plot or scenes; just establish who these people are and \
what pressures them."""

TASK = "Write the Characters section, grounded in the world and magic system above."
