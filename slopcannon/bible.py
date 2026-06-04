"""The shared story bible — the evolving canonical truth.

In the MVP this is deliberately the simplest thing that could work: a dict of
markdown strings, one section per stage, rendered to a single document. Because
the pipeline is sequential and each section has exactly one author, there are
no concurrent writes and no "which version is canonical" question to answer.

The one invariant we *do* encode here, because it is central to the learning
goal, is single-author-per-section: committing a section that already exists
raises unless you explicitly overwrite. That makes "exactly one current truth,
written once" a property the code enforces rather than a convention we hope for.
When we later add revision loops, the place that pain shows up is this method.
"""

from __future__ import annotations

# Fixed render order. Also the canonical list of valid section keys.
SECTION_ORDER: tuple[str, ...] = (
    "premise",
    "world",
    "magic",
    "characters",
    "plot",
    "prose",
)

# Human-facing headings for rendering.
SECTION_TITLES: dict[str, str] = {
    "premise": "Premise",
    "world": "World",
    "magic": "Magic System",
    "characters": "Characters",
    "plot": "Plot",
    "prose": "Story",
}


class StoryBible:
    """An ordered collection of markdown sections forming the canonical truth."""

    def __init__(self) -> None:
        self._sections: dict[str, str] = {}

    def set(self, key: str, content: str, *, overwrite: bool = False) -> None:
        """Commit a section. Raises on unknown keys, or on re-writing an
        existing section unless ``overwrite=True`` (the MVP never overwrites).
        """
        if key not in SECTION_ORDER:
            raise KeyError(
                f"Unknown section {key!r}. Valid: {', '.join(SECTION_ORDER)}"
            )
        if key in self._sections and not overwrite:
            raise ValueError(
                f"Section {key!r} is already committed. In the MVP each section "
                f"has exactly one author and is written once. Pass overwrite=True "
                f"only when you mean to replace canonical truth."
            )
        self._sections[key] = content.strip()

    def get(self, key: str) -> str:
        """Return a committed section's content, or raise if absent."""
        if key not in self._sections:
            raise KeyError(f"Section {key!r} has not been committed yet.")
        return self._sections[key]

    def has(self, key: str) -> bool:
        return key in self._sections

    def populated_sections(self) -> list[str]:
        """Committed section keys, in canonical order."""
        return [k for k in SECTION_ORDER if k in self._sections]

    def render(self, *, include: tuple[str, ...] | None = None) -> str:
        """Render committed sections as one markdown document, in canonical
        order. ``include`` optionally restricts to a subset of keys (used to,
        e.g., render the bible without the prose for the prose writer).
        """
        keys = self.populated_sections()
        if include is not None:
            keys = [k for k in keys if k in include]
        if not keys:
            return "_(empty bible)_"
        parts = []
        for key in keys:
            parts.append(f"## {SECTION_TITLES[key]}\n\n{self._sections[key]}")
        return "\n\n".join(parts)
