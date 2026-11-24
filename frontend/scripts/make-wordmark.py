"""Le logo « tRoolPlay » en tracés vectoriels, tirés des polices une fois pour toutes (#108).

Le site n'a pas à télécharger trois polices pour neuf lettres. Ce script écrit
src/components/wordmarkPaths.ts ; on ne le relance que si le logo change.

    uv run --no-project --with fonttools --with brotli python scripts/make-wordmark.py

Polices : IM Fell English et IM Fell DW Pica (SIL Open Font License), via @fontsource.
"""

from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FILES = Path(__file__).parent.parent / "node_modules" / "@fontsource"
ROMAN = FILES / "im-fell-english/files/im-fell-english-latin-400-normal.woff2"
ITALIC = FILES / "im-fell-english/files/im-fell-english-latin-400-italic.woff2"
PICA = FILES / "im-fell-dw-pica/files/im-fell-dw-pica-latin-400-italic.woff2"

# Chaque lettre : sa police, si elle ressort (R et P), et un rapprochement en fraction de cadratin.
LETTERS = [
    ("t", ROMAN, False, 0),
    ("R", ITALIC, True, 0),
    ("o", ROMAN, False, 0),
    ("o", ROMAN, False, 0),
    ("l", ROMAN, False, 0),
    ("P", PICA, True, -0.08),
    ("l", ROMAN, False, 0),
    ("a", ROMAN, False, 0),
    ("y", ROMAN, False, 0),
]

fonts: dict[Path, TTFont] = {}
x = 0.0
plain, marked = [], []
top, bottom = 0.0, 0.0
for char, file, accent, nudge in LETTERS:
    font = fonts.setdefault(file, TTFont(file))
    em = font["head"].unitsPerEm
    scale = 1000 / em  # tout ramené à 1000 unités par cadratin
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(char)]
    x += nudge * 1000
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.0f}")
    gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, 0)))
    (marked if accent else plain).append(pen.getCommands())
    x += gs[name].width * scale
    top = max(top, font["hhea"].ascent * scale)
    bottom = min(bottom, font["hhea"].descent * scale)

out = Path(__file__).parent.parent / "src/components/wordmarkPaths.ts"
out.write_text(
    "// Écrit par scripts/make-wordmark.py : ne pas modifier à la main.\n"
    f"export const WORDMARK_VIEWBOX = '0 {-top:.0f} {x:.0f} {top - bottom:.0f}'\n"
    f"export const WORDMARK_PLAIN = '{' '.join(plain)}'\n"
    f"export const WORDMARK_MARKED = '{' '.join(marked)}'\n"
)
print("écrit :", out.name, f"{out.stat().st_size} octets, largeur {x:.0f}")
