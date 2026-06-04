"""Render bible/story markdown to a self-contained dark-theme HTML page.

A reading aid, nothing more: the canonical artifacts stay markdown; this just
wraps them in a single static file (inline CSS, no assets) that's pleasant to
read in a browser. Used by the RunLogger to emit story.html / bible.html.
"""

from __future__ import annotations

from html import escape

import markdown as _markdown

# Dark, serif, single readable column. Scene-break `---` (markdown -> <hr>) is
# rendered as a centered "* * *". Inline so the file is fully self-contained.
_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #15161a;
  color: #d7d8dc;
  font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
  font-size: 19px;
  line-height: 1.7;
}
main { max-width: 38rem; margin: 0 auto; padding: 3.5rem 1.5rem 6rem; }
h1, h2, h3 {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #f2f3f5; line-height: 1.25; margin-top: 2.2em;
}
h1 { font-size: 1.9rem; }
h2 { font-size: 1.4rem; border-bottom: 1px solid #2c2e36; padding-bottom: .3em; }
h3 { font-size: 1.1rem; color: #b9bcc4; }
p { margin: 0 0 1.2em; }
em { color: #e7c98a; font-style: italic; }
strong { color: #f2f3f5; }
a { color: #7fb2ff; }
hr { border: none; text-align: center; margin: 2.5em 0; }
hr::after { content: "* * *"; color: #6a6d77; letter-spacing: .5em; }
blockquote {
  border-left: 3px solid #2c2e36; margin: 0 0 1.2em; padding-left: 1em; color: #aeb0b8;
}
code { background: #232531; padding: .1em .35em; border-radius: 4px; font-size: .85em; }
ul, ol { padding-left: 1.3em; }
li { margin: .3em 0; }
.title { font-size: 2rem; margin: 0 0 2rem; }
"""

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<main>
<h1 class="title">{title}</h1>
{body}
</main>
</body>
</html>
"""


def render_page(title: str, markdown_text: str) -> str:
    """Wrap markdown in a self-contained dark-theme HTML page."""
    body = _markdown.markdown(markdown_text, extensions=["extra", "sane_lists"])
    return _TEMPLATE.format(title=escape(title), css=_CSS, body=body)
