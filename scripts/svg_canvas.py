"""Build self-contained README SVGs from local fonts, icons, and verified data.

Text is outlined for identical typography on GitHub, without remote font requests.
No JavaScript, external SVG resources, or foreignObject elements are emitted.
"""
from functools import lru_cache
from html import escape
from pathlib import Path
import json

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets/generated"
SVG = "http://www.w3.org/2000/svg"
SETTINGS = json.loads((ROOT / "data/portfolio.json").read_text(encoding="utf-8"))
COLORS = SETTINGS["colors"]
WHITE, MUTED, BLUE = COLORS["text"], COLORS["muted"], COLORS["accent"]


@lru_cache(maxsize=None)
def font(mono=False, weight=500):
    filename = "JetBrainsMono.ttf" if mono else "Manrope.ttf"
    loaded = TTFont(ROOT / "assets/fonts" / filename)
    return instantiateVariableFont(loaded, {"wght": weight}, inplace=True)


class Canvas:
    def __init__(self, width, height, title, description):
        self.width, self.height = width, height
        self.title, self.description = title, description
        self.light = False
        self.body, self.glyphs = [], {}

    def add(self, markup):
        self.body.append(markup)

    def rect(self, x, y, width, height, fill, radius=0, stroke=None, **attrs):
        extra = " ".join(f'{key.replace("_", "-")}="{value}"' for key, value in attrs.items())
        self.add(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}"'
                 + (f' stroke="{stroke}"' if stroke else "") + f' {extra}/>')

    def line(self, x1, y1, x2, y2, stroke="#26384c", **attrs):
        extra = " ".join(f'{key.replace("_", "-")}="{value}"' for key, value in attrs.items())
        self.add(f'<path d="M{x1} {y1}H{x2}" stroke="{stroke}" {extra}/>' if y1 == y2 else
                 f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{stroke}" {extra}/>')

    def measure(self, text, size, mono=False, weight=500, spacing=0):
        f = font(mono, weight)
        cmap, metrics = f.getBestCmap(), f["hmtx"].metrics
        return sum(metrics[cmap[ord(char)]][0] for char in text) * size / f["head"].unitsPerEm + max(0, len(text) - 1) * spacing

    def text(self, text, x, y, size=16, fill=WHITE, weight=500, mono=False, spacing=0, align="left"):
        f = font(mono, weight)
        scale = size / f["head"].unitsPerEm
        if align != "left":
            x -= self.measure(text, size, mono, weight, spacing) * (0.5 if align == "center" else 1)
        cmap, glyph_set = f.getBestCmap(), f.getGlyphSet()
        runs = []
        for char in text:
            name = cmap[ord(char)]
            identifier = f'g{int(mono)}w{weight}c{ord(char)}'
            if identifier not in self.glyphs:
                pen = SVGPathPen(glyph_set)
                glyph_set[name].draw(pen)
                self.glyphs[identifier] = pen.getCommands()
            runs.append(f'<use href="#{identifier}" transform="translate({x:.3f} {y}) scale({scale:.6f} {-scale:.6f})"/>')
            x += f["hmtx"].metrics[name][0] * scale + spacing
        self.add(f'<g fill="{fill}" aria-label="{escape(text, quote=True)}">' + "".join(runs) + "</g>")

    def paragraph(self, text, x, y, width, size=15, leading=24, fill=MUTED, max_lines=None):
        line, lines = "", []
        for word in text.split():
            test = (line + " " + word).strip()
            if self.measure(test, size) > width and line:
                lines.append(line)
                line = word
            else:
                line = test
        if line:
            lines.append(line)
        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines]
            final = lines[-1]
            while final and self.measure(final + "...", size) > width:
                final = final[:-1]
            lines[-1] = final.rstrip() + "..."
        for i, line in enumerate(lines):
            self.text(line, x, y + i * leading, size, fill)
        return len(lines) * leading

    def shell(self):
        self.rect(1, 1, self.width - 2, self.height - 2, "#0d1117", 22)
        self.rect(1, 1, self.width - 2, self.height - 2, "url(#atmosphere)", 22)
        self.rect(1, 1, self.width - 2, self.height - 2, "url(#green)", 22)
        self.rect(1, 1, self.width - 2, self.height - 2, "url(#violet)", 22)
        self.rect(1, 1, self.width - 2, self.height - 2, "none", 22, "#316c98")

    def header(self, index, label, subtitle, mobile=False):
        self.text(index + " / " + label, 30, 43, 12, BLUE, 600, True, 1.6)
        self.text(subtitle, 30, 78, 23 if mobile else 27, WHITE, 800)
        self.line(30, 101, self.width - 30, 101, "#2c5375")

    def save(self, name):
        definitions = '''<radialGradient id="atmosphere" cx=".17" cy="0" r=".7" gradientTransform="scale(1 .85)">
          <stop offset="0" stop-color="#397ec5" stop-opacity=".46"/>
          <stop offset="1" stop-color="#397ec5" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="green" cx=".83" cy=".06" r=".65">
          <stop stop-color="#3fb950" stop-opacity=".12"/><stop offset="1" stop-color="#3fb950" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="violet" cx=".70" cy="1.12" r=".65">
          <stop stop-color="#a371f7" stop-opacity=".30"/><stop offset="1" stop-color="#a371f7" stop-opacity="0"/>
        </radialGradient>'''
        definitions += "".join(f'<path id="{key}" d="{value}"/>' for key, value in self.glyphs.items())
        result = (f'<svg xmlns="{SVG}" xmlns:xlink="http://www.w3.org/1999/xlink" width="{self.width}" height="{self.height}" '
                  f'viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title desc">'
                  f'<title id="title">{escape(self.title)}</title><desc id="desc">{escape(self.description)}</desc>'
                  f'<defs>{definitions}</defs>' + "".join(self.body) + '</svg>\n')
        # xlink keeps glyph references compatible with older SVG renderers.
        result = result.replace(' href="#', ' xlink:href="#')
        replacements = {
            "#0d1117": COLORS["background"], "#101822": COLORS["surface"],
            "#316c98": COLORS["border"], "#397ec5": COLORS["blue_glow"],
            "#3fb950": COLORS["green_glow"], "#a371f7": COLORS["violet_glow"],
        }
        for old, new in replacements.items():
            result = result.replace(old, new)
        if self.light:
            for old, new in {
                COLORS["background"]: "#f6f8fa", COLORS["surface"]: "#ffffff",
                WHITE: "#1f2328", MUTED: "#526170", BLUE: "#0969da",
                COLORS["border"]: "#8caeca", "#2c5375": "#c5d5e5",
                "#26384c": "#d1d9e0", "#1b2531": "#dce5ee",
                "#203f60": "#b7d5ef", "#2c6090": "#78add8",
                "#3983bd": "#347fb9",
            }.items():
                result = result.replace(old, new)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / name).write_text(result, encoding="utf-8")

