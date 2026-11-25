"""Build self-contained README SVGs from local fonts, icons, and verified data.

Text is outlined for identical typography on GitHub, without remote font requests.
No JavaScript, external SVG resources, or foreignObject elements are emitted.
"""
from base64 import b64encode
from datetime import date, datetime, timedelta
from functools import lru_cache
from html import escape
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets/generated"
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
WHITE, MUTED, BLUE = "#e6edf3", "#a7b2bf", "#58a6ff"


@lru_cache(maxsize=None)
def font(mono=False, weight=500):
    filename = "JetBrainsMono.ttf" if mono else "Manrope.ttf"
    loaded = TTFont(ROOT / "assets/fonts" / filename)
    return instantiateVariableFont(loaded, {"wght": weight}, inplace=True)


class Canvas:
    def __init__(self, width, height, title, description):
        self.width, self.height = width, height
        self.title, self.description = title, description
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

    def paragraph(self, text, x, y, width, size=15, leading=24, fill=MUTED):
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
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / name).write_text(result, encoding="utf-8")


def arrow(canvas, x, y, color=BLUE):
    canvas.add(f'<path d="M{x} {y+9}l12-12m-10 0h10v10" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')


def hero(mobile=False):
    w, h = (480, 384) if mobile else (960, 300)
    c = Canvas(w, h, "Dipesh Katuwal — aspiring full-stack developer", "Software engineering student building with React, Spring Boot, and databases.")
    c.shell()
    c.rect(25, 25, w - 50, h - 50, "#0b1119", 20, "#2c6086", fill_opacity=".66")
    # Embed the actual avatar so GitHub never has to fetch an SVG subresource.
    cx, cy, r = (73, 80, 28) if mobile else (112, 128, 48)
    c.add(f'<defs><clipPath id="avatar"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath></defs>')
    avatar = b64encode((ROOT / "assets/avatar.jpg").read_bytes()).decode()
    c.add(f'<circle cx="{cx}" cy="{cy}" r="{r+4}" fill="none" stroke="{BLUE}" stroke-width="1.5"/>')
    c.add(f'<image x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" clip-path="url(#avatar)" xlink:href="data:image/jpeg;base64,{avatar}"/>')
    if mobile:
        c.text("@Dipesh-Katuwal", 117, 77, 14, MUTED, 500, True)
        c.text("SOFTWARE ENGINEERING STUDENT", 117, 98, 10.5, BLUE, 600, True, .3)
        c.text("Dipesh Katuwal", 46, 168, 38, WHITE, 800)
        c.text("Aspiring Full-Stack Developer", 46, 205, 19, MUTED, 500)
        c.line(46, 229, 434, 229)
        c.text("REACT", 46, 266, 12, BLUE, 600, True, 1)
        c.text("SPRING BOOT", 166, 266, 12, BLUE, 600, True, 1)
        c.text("MYSQL", 360, 266, 12, BLUE, 600, True, 1)
        c.line(102, 262, 149, 262)
        c.line(278, 262, 343, 262)
        c.text("Interfaces. APIs. Useful software.", 46, 319, 14, WHITE, 600)
    else:
        c.text("@Dipesh-Katuwal", 198, 84, 13, MUTED, 600, True, 1.1)
        c.text("Dipesh Katuwal", 194, 148, 58, WHITE, 800)
        c.text("Software Engineering Student", 198, 184, 20, MUTED, 500)
        c.text("Aspiring Full-Stack Developer", 198, 212, 20, MUTED, 500)
        c.text("INTERFACES  /  APIS  /  USEFUL SOFTWARE", 48, 265, 10.5, BLUE, 600, True, 1.2)
        c.rect(771, 47, 139, 25, "#132337", 12, "#2c5375")
        c.text("BUILD. LEARN. REPEAT.", 840, 63, 8, BLUE, 600, True, align="center")
        for i in range(3):
            c.rect(802 + i*39, 223, 12, 12, "#102137", 3, "#316c98")
            if i < 2:
                c.line(814 + i*39, 229, 841 + i*39, 229, "#316c98")
    c.save("hero-mobile.svg" if mobile else "hero.svg")


def icon(canvas, technology, x, y, size):
    root = ET.parse(ROOT / f"assets/icons/{technology}.svg").getroot()
    root.set("x", str(x)); root.set("y", str(y))
    root.set("width", str(size)); root.set("height", str(size))
    canvas.add(ET.tostring(root, encoding="unicode"))


def stack(mobile=False):
    w, h = (480, 273) if mobile else (960, 163)
    c = Canvas(w, h, "Technology stack", "Java, Spring Boot, React, JavaScript, TypeScript, and MySQL. Technology logos indicate tools I use, not proficiency scores.")
    c.shell()
    c.text("THE TOOLKIT", 30, 37, 11, BLUE, 600, True, 1.6)
    technologies = [("java", "Java"), ("spring", "Spring Boot"), ("react", "React"), ("javascript", "JavaScript"), ("typescript", "TypeScript"), ("mysql", "MySQL")]
    for i, (key, label) in enumerate(technologies):
        col, row = (i % 3, i // 3) if mobile else (i, 0)
        cell_w = 140 if mobile else 148
        x = 30 + col*cell_w
        y = 57 + row*100
        c.rect(x, y, cell_w-10, 84, "#101822", 12, "#24384c")
        icon(c, key, x+(cell_w-10-30)/2, y+12, 30)
        c.text(label, x+(cell_w-10)/2, y+65, 14 if mobile else 13, WHITE, 600, align="center")
    c.save("stack-mobile.svg" if mobile else "stack.svg")


def projects(mobile=False):
    records = json.loads((ROOT / "data/projects.json").read_text(encoding="utf-8"))
    w, h = (480, 1142) if mobile else (960, 638)
    c = Canvas(w, h, "Selected projects — Dipesh Katuwal", "Four learning projects: BillingSoftware, AiResumeAnalyzer, DarazClone, and EMS. Repository links and descriptions follow this image in the README.")
    c.shell()
    c.header("01", "PROJECTS.LIST", "Selected work", mobile)
    if not mobile:
        c.text("./projects.sh --selected", 930, 78, 11, MUTED, 500, True, align="right")
    for i, p in enumerate(records):
        x = 30 if mobile else 30 + (i % 2)*458
        y = 124 + i*248 if mobile else 124 + (i // 2)*248
        cw, ch = (420, 232) if mobile else (442, 232)
        c.rect(x, y, cw, ch, "#0c121a", 14, "#2d6089")
        c.rect(x+1, y+1, cw-2, 33, "#151f2c", 13)
        c.rect(x+1, y+20, cw-2, 14, "#151f2c")
        c.line(x, y+34, x+cw, y+34, "#2a4c6a")
        c.add(f'<circle cx="{x+17}" cy="{y+17}" r="2.2" fill="{BLUE}"/>')
        c.text(p["repository"], x+28, y+21, 12 if mobile else 11, MUTED, 500, True)
        c.text(f"0{i+1}", x+cw-18, y+22, 10, BLUE, 500, True, align="right")
        c.text(p["title"], x+20, y+73, 23 if mobile else 24, WHITE, 800)
        c.paragraph(p["description"], x+20, y+105, cw-42, 16 if mobile else 15, 23)
        tx = x+20
        for tech in p["technologies"]:
            tag_size = 12 if mobile else 11
            tw = c.measure(tech, tag_size, True) + 18
            c.rect(tx, y+171, round(tw, 2), 23, "#142337", 11, "#2b4d6b")
            c.text(tech, tx+9, y+187, tag_size, BLUE, 500, True)
            tx += tw+8
        c.text(p["category"], x+20, y+216, 10 if mobile else 9, MUTED, 500, True, .7)
    c.save("projects-mobile.svg" if mobile else "projects.svg")


def snake_path(cells, origin, step):
    """Chronological route through actual active cells, using axis-aligned steps."""
    points = [(col, row) for col, row, level in cells if level > 0]
    if not points:
        return ""
    grid = [points[0]]
    x, y = points[0]
    for tx, ty in points[1:]:
        while x != tx:
            x += 1 if tx > x else -1
            grid.append((x, y))
        while y != ty:
            y += 1 if ty > y else -1
            grid.append((x, y))
    # Return below the grid so the animation has a continuous closed path.
    grid += [(x, 8), (points[0][0], 8), points[0]]
    return "M" + " L".join(f"{origin[0]+x*step:.2f} {origin[1]+y*step:.2f}" for x, y in grid) + " Z"


def activity(mobile=False, static=False):
    data = json.loads((ROOT / "data/profile.json").read_text(encoding="utf-8"))
    w, h = (480, 465) if mobile else (960, 420)
    description = (f"{data['contributions_last_year']} contributions in the last year; {data['public_repositories']} public repositories; "
                   f"{data['active_days_in_grid']} active days in the displayed grid. Snapshot from {data['updated_at']}. "
                   "Blue cells show real GitHub contribution intensity. A decorative snake follows active cells; this is not a live feed.")
    c = Canvas(w, h, "GitHub activity — public contribution snapshot", description)
    c.shell()
    c.header("02", "ACTIVITY.LOG", "Small steps. Steady progress.", mobile)
    stat_width = (w-60)/3
    for i, (value, label) in enumerate([(data["contributions_last_year"], "CONTRIBUTIONS"), (data["active_days_in_grid"], "ACTIVE DAYS"), (data["public_repositories"], "PUBLIC REPOS")]):
        x = 30+i*stat_width
        c.text(str(value), x+15, 158, 34, WHITE, 800)
        c.text(label, x+15, 182, 8.5 if mobile else 10, MUTED, 500, True, .8)
        if i < 2:
            c.line(x+stat_width-12, 124, x+stat_width-12, 185)
    start = date.fromisoformat(data["calendar_start"])
    start -= timedelta(days=(start.weekday()+1) % 7)
    cells = []
    for day in data["days"]:
        offset = (date.fromisoformat(day["date"])-start).days
        cells.append((offset//7, offset % 7, day["level"]))
    columns = max(cell[0] for cell in cells)+1
    step = (w-76) / columns
    size = step-3 if not mobile else step-1.8
    origin = (38+size/2, 228+size/2)
    colors = ["#1b2531", "#203f60", "#2c6090", "#3983bd", "#58a6ff"]
    for col, row, level in cells:
        c.rect(round(38+col*step, 2), round(228+row*step, 2), round(size, 2), round(size, 2), colors[level], 2 if mobile else 3)
    path = snake_path(cells, origin, step)
    if path and not static:
        c.add(f'<defs><path id="route" d="{path}"/></defs>')
        for segment in range(5, -1, -1):
            opacity = 1 - segment*.13
            c.add(f'<g opacity="{opacity:.2f}"><rect x="{-size/2:.2f}" y="{-size/2:.2f}" width="{size:.2f}" height="{size:.2f}" rx="{max(2,size*.3):.2f}" fill="{WHITE if segment == 0 else BLUE}"/>')
            if segment == 0 and not mobile:
                c.add('<circle cx="-2.2" cy="-1.5" r="1.3" fill="#15385b"/><circle cx="2.2" cy="-1.5" r="1.3" fill="#15385b"/>')
            c.add(f'<animateMotion dur="48s" begin="{-12-segment*.18:.2f}s" repeatCount="indefinite" calcMode="paced"><mpath xlink:href="#route"/></animateMotion></g>')
    footer_y = 345 if mobile else 379
    if mobile:
        c.text("LAST YEAR / PUBLIC GITHUB ACTIVITY", 30, 330, 9, BLUE, 500, True, .6)
        c.text("Contribution intensity", 30, 360, 11, MUTED)
        for i, color in enumerate(colors):
            c.rect(341+i*17, 349, 11, 11, color, 2)
        c.text("Updated " + datetime.fromisoformat(data["updated_at"]).strftime("%d %b %Y"), 30, 407, 10, MUTED, 500, True)
        c.text("Snapshot, not a live feed.", 30, 430, 10, MUTED, 500, True)
    else:
        c.text("LAST YEAR / PUBLIC GITHUB ACTIVITY", 30, footer_y, 9, BLUE, 500, True, .8)
        c.text("Updated " + datetime.fromisoformat(data["updated_at"]).strftime("%d %b %Y") + " UTC", 930, footer_y, 10, MUTED, 500, True, align="right")
        c.text("Less", 774, 208, 8, MUTED, 500, True)
        for i, color in enumerate(colors):
            c.rect(807+i*17, 200, 10, 10, color, 2)
        c.text("More", 927, 208, 8, MUTED, 500, True, align="right")
    suffix = ("-mobile" if mobile else "") + ("-static" if static else "")
    c.save(f"activity{suffix}.svg")


def footer(mobile=False):
    w, h = (480, 111) if mobile else (960, 111)
    c = Canvas(w, h, "Explore Dipesh Katuwal on GitHub", "github.com/Dipesh-Katuwal")
    c.shell()
    c.text("LET'S BUILD SOMETHING USEFUL.", w/2, 40, 10, BLUE, 600, True, 1.1, align="center")
    c.text("github.com/Dipesh-Katuwal", w/2, 73, 16, WHITE, 700, align="center")
    c.save("footer-mobile.svg" if mobile else "footer.svg")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--activity-only", action="store_true")
    args = parser.parse_args()
    for mobile in (False, True):
        if not args.activity_only:
            hero(mobile); stack(mobile); projects(mobile); footer(mobile)
        activity(mobile)
        activity(mobile, static=True)
    print("Built " + ("activity snapshots." if args.activity_only else "all README assets."))


if __name__ == "__main__":
    main()
