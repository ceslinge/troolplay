"""L'icône d'onglet : une lettre d'IM Fell English sur un rond de cire (#108).

Le t droit, première lettre du logo « tRoolPlay ». Le tracé est tiré de la police, pour que
l'icône n'ait besoin d'aucune police. On ne la relance que si l'icône change :

    uv run --no-project --with fonttools --with brotli python scripts/make-favicon.py \
        node_modules/@fontsource/im-fell-english/files/im-fell-english-latin-400-normal.woff2 \
        public/favicon.svg t
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
font = TTFont(sys.argv[1])
gs = font.getGlyphSet()
letter = sys.argv[3] if len(sys.argv) > 3 else "R"
glyph = gs[font.getBestCmap()[ord(letter)]]
b = BoundsPen(gs); glyph.draw(b)
x0, y0, x1, y1 = b.bounds
height = 60.0
s = height / (y1 - y0)
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
# Retourner l'axe vertical, centrer dans un carré de 100, un peu à gauche : l'italique penche.
pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
glyph.draw(TransformPen(pen, (s, 0, 0, -s, 49 - cx * s, 51 + cy * s)))
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <!-- Une lettre d'IM Fell English (SIL Open Font License), sur un rond de cire. -->
  <circle cx="50" cy="50" r="48" fill="#7a2e1c"/>
  <circle cx="50" cy="50" r="44" fill="none" stroke="#5c2014" stroke-width="3"/>
  <path fill="#f3d9c2" d="{pen.getCommands()}"/>
</svg>"""
open(sys.argv[2], "w").write(svg + "\n")
print(len(svg), "octets écrits dans", sys.argv[2])
