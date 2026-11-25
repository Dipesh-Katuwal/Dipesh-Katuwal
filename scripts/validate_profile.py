"""Validate the portfolio, verified snapshot, local assets, and optional live links."""
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from refresh_data import streaks

ROOT = Path(__file__).resolve().parents[1]
SVG = "{http://www.w3.org/2000/svg}"


class ReadmeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.picture_sources = []
        self.link = None
        self.linked_projects = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        assert tag not in {"script", "style", "iframe", "svg"}, f"Unsupported README tag: {tag}"
        assert not any(key.startswith("on") or key == "style" for key in attrs), "Unexpected active HTML or CSS"
        if tag == "a":
            self.link = attrs.get("href")
        if tag == "picture":
            self.picture_sources.append([])
        if tag == "source":
            self.picture_sources[-1].append(attrs)
        if tag == "img":
            assert attrs.get("alt"), "Image needs alternative text"
            if attrs["src"].startswith("assets/generated/project-"):
                assert self.link and self.link.startswith("https://github.com/"), "Project card is not linked"
                self.linked_projects.append(self.link)
        for key in ("src", "srcset", "href"):
            if key in attrs:
                self.references.append(attrs[key])

    def handle_endtag(self, tag):
        if tag == "a":
            self.link = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-links", action="store_true")
    args = parser.parse_args()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    settings = json.loads((ROOT/"data/portfolio.json").read_text(encoding="utf-8"))
    projects = json.loads((ROOT/"data/projects.json").read_text(encoding="utf-8"))
    assert settings["typing_lines"] and len(settings["typing_lines"]) <= 5, "Configure one to five typing lines"
    assert all(1 <= len(group["items"]) <= 3 for group in settings["technology_groups"]), "Use one to three tools per group"
    assert all(re.fullmatch(r'#[0-9a-fA-F]{6}', value) for value in settings["colors"].values()), "Use six-digit hexadecimal colors"
    assert len({p["repository"] for p in projects}) == len(projects), "Duplicate featured repository"
    assert all(len(p.get("technologies", [])) <= 3 for p in projects), "Use up to three labels per project"
    document = ReadmeParser()
    document.feed(readme)
    document.references += re.findall(r'\]\(([^)]+)\)', readme)
    assert len(document.linked_projects) == len(projects), "Featured card missing"
    assert all(any("max-width" in source.get("media", "") for source in sources) for sources in document.picture_sources), "Missing mobile variant"
    assert any("prefers-reduced-motion" in source["media"] for sources in document.picture_sources for source in sources)
    assert any("prefers-color-scheme: light" in source["media"] for sources in document.picture_sources for source in sources)
    headings = {re.sub(r'[^a-z0-9 -]', '', value.lower()).replace(' ', '-') for value in re.findall(r'^## (.+)$', readme, re.M)}
    links = set(document.references)
    for reference in sorted(links):
        if reference.startswith("#"):
            assert reference[1:] in headings, f"Missing navigation heading {reference}"
        elif reference.startswith(("https://", "mailto:")):
            parsed = urlparse(reference)
            assert not parsed.username and not parsed.password, "Credentials must not appear in public links"
            if args.check_links and reference.startswith("https://"):
                request = urllib.request.Request(reference, headers={"User-Agent":"Dipesh-Katuwal-portfolio/2.0"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    assert response.status == 200, reference
        else:
            assert (ROOT/reference).is_file(), f"Missing local reference: {reference}"
    referenced = {r for r in links if r.startswith("assets/generated/")}
    files = list((ROOT/"assets/generated").glob("*.svg"))
    assert referenced == {file.relative_to(ROOT).as_posix() for file in files}, "Missing or unused generated SVGs"
    for file in files:
        root = ET.parse(file).getroot()
        assert root.tag == SVG+"svg" and root.get("viewBox"), file
        assert root.find(SVG+"title") is not None and root.find(SVG+"desc") is not None, file
        identifiers = [node.get("id") for node in root.iter() if node.get("id")]
        assert len(identifiers) == len(set(identifiers)), f"Duplicate SVG ID: {file}"
        animations = []
        for node in root.iter():
            assert node.tag not in {SVG+"script", SVG+"foreignObject"}, file
            if node.tag in {SVG+"animate", SVG+"animateMotion"}:
                animations.append(node)
                if node.get("keyTimes"):
                    times=[float(v) for v in node.get("keyTimes").split(';')]
                    assert times[0] == 0 and times[-1] == 1 and times == sorted(times), file
                    assert len(times) == len(node.get("values").split(';')), file
            for key,value in node.attrib.items():
                if key.endswith("href"):
                    assert value.startswith(("#", "data:image/jpeg;base64,")), f"External SVG dependency: {file}"
                    if value.startswith("#"):
                        assert value[1:] in identifiers, f"Broken SVG glyph reference: {file}"
        if "static" in file.stem:
            assert not animations, f"Reduced-motion asset still animates: {file}"
    data = json.loads((ROOT/"data/profile.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 2
    days = data["days"]
    assert 350 <= len(days) <= 378
    assert all((date.fromisoformat(b["date"])-date.fromisoformat(a["date"])).days == 1 for a,b in zip(days,days[1:])), "Calendar gap"
    assert data["active_days_in_grid"] == sum(d["level"] > 0 for d in days)
    assert data["streak"] == streaks(days,date.fromisoformat(data["streak"]["as_of"]))
    assert data["public_repositories"] == len(set(data["repositories"]))
    years = data["contributions_by_year"]
    assert [y["year"] for y in years] == list(range(data["joined_year"],datetime.fromisoformat(data["updated_at"]).year+1))
    assert data["contributions_since_joining"] == sum(y["contributions"] for y in years)
    assert not set(settings["language_exclusions"]) & set(data["language_repositories"])
    assert all(isinstance(n,int) and n >= 0 for n in data["languages"].values())
    assert all(p["repository"] in data["repositories"] and p["repository"] in data["featured"] for p in projects)
    now=datetime.fromisoformat(data["updated_at"])
    assert all(now-timedelta(days=30) <= datetime.fromisoformat(e["created_at"].replace("Z","+00:00")) <= now for e in data["recent_events"])
    assert "Hi there" not in readme and "github-readme-stats.vercel.app" not in readme
    total=sum(file.stat().st_size for file in files)
    print(f"Validated {len(files)} local SVGs ({total/1024:.0f} KiB across all variants), linked cards, navigation, motion/theme sources, and snapshot calculations.")
    if args.check_links:
        print("All public README HTTPS links returned HTTP 200.")


if __name__ == "__main__":
    main()
