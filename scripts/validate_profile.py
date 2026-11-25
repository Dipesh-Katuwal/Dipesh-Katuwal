"""Check the generated deliverables, data invariants, and optional remote links."""
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"


class ReadmeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.pictures = 0
        self.sources = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        assert tag not in {"script", "style", "iframe", "svg"}, f"Unsupported README tag: {tag}"
        assert not any(key.startswith("on") or key == "style" for key in attrs), "Unexpected active HTML or CSS"
        if tag == "picture":
            self.pictures += 1
        if tag == "source":
            self.sources += 1
        if tag == "img":
            assert attrs.get("alt"), "Image needs alternative text"
        for key in ("src", "srcset", "href"):
            if key in attrs:
                self.references.append(attrs[key])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-links", action="store_true")
    args = parser.parse_args()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    document = ReadmeParser()
    document.feed(readme)
    document.references += re.findall(r'\]\(([^)]+)\)', readme)
    assert document.pictures == 5 and document.sources == 7, "Missing responsive or motion sources"
    for reference in set(document.references):
        if reference.startswith("https://"):
            if args.check_links:
                request = urllib.request.Request(reference, headers={"User-Agent": "Dipesh-Katuwal-profile/1.0"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    assert response.status == 200, reference
        else:
            assert (ROOT / reference).is_file(), f"Missing image or file: {reference}"
    files = list((ROOT / "assets/generated").glob("*.svg"))
    assert len(files) == 12, "Missing generated assets"
    for file in files:
        tree = ET.parse(file)
        root = tree.getroot()
        assert root.tag == SVG + "svg"
        assert root.find(SVG + "title") is not None and root.find(SVG + "desc") is not None
        assert root.get("viewBox"), file
        identifiers = [node.get("id") for node in root.iter() if node.get("id")]
        assert len(identifiers) == len(set(identifiers)), f"Duplicate SVG IDs: {file}"
        for node in root.iter():
            assert node.tag not in {SVG + "script", SVG + "foreignObject"}
            for key, value in node.attrib.items():
                if key.endswith("href"):
                    assert value.startswith("#") or value.startswith("data:image/jpeg;base64,"), f"External SVG resource: {file}"
                    if value.startswith("#"):
                        assert value[1:] in identifiers, f"Missing glyph/path reference: {file}"
        assert ("animateMotion" in file.read_text(encoding="utf-8")) == (file.stem in {"activity", "activity-mobile"}), file
    snapshot = json.loads((ROOT / "data/profile.json").read_text(encoding="utf-8"))
    days = snapshot["days"]
    assert 350 <= len(days) <= 378
    assert all((date.fromisoformat(b["date"])-date.fromisoformat(a["date"])).days == 1 for a,b in zip(days, days[1:])), "Calendar has gaps"
    assert snapshot["active_days_in_grid"] == sum(day["level"] > 0 for day in days)
    assert snapshot["public_repositories"] == len(set(snapshot["repositories"]))
    projects = json.loads((ROOT / "data/projects.json").read_text(encoding="utf-8"))
    assert all(p["repository"] in snapshot["repositories"] and p["evidence"] for p in projects)
    total = sum(file.stat().st_size for file in files)
    print(f"Validated {len(files)} SVGs ({total/1024:.0f} KiB total), responsive README references, and public data invariants.")
    if args.check_links:
        print("All README HTTPS links returned HTTP 200.")


if __name__ == "__main__":
    main()
