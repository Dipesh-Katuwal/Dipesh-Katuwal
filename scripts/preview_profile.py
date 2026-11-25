"""Preview GitHub's own sanitized Markdown output without publishing changes."""
from html.parser import HTMLParser
from pathlib import Path
import json
import os
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


class RenderedCards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.link = None
        self.cards = 0
        self.sources = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "a":
            self.link = attrs.get("href")
        if tag == "source":
            self.sources += 1
        if tag == "img" and attrs.get("src", "").startswith("assets/generated/project-"):
            if not self.link or not self.link.startswith("https://github.com/"):
                raise ValueError("GitHub did not preserve a card's repository link")
            self.cards += 1

    def handle_endtag(self, tag):
        if tag == "a":
            self.link = None


def main():
    settings = json.loads((ROOT/"data/portfolio.json").read_text(encoding="utf-8"))
    projects = json.loads((ROOT/"data/projects.json").read_text(encoding="utf-8"))
    payload = json.dumps({"text": (ROOT/"README.md").read_text(encoding="utf-8"), "mode":"gfm", "context":settings["username"]+"/"+settings["username"]}).encode()
    headers = {"User-Agent":"Dipesh-Katuwal-portfolio-preview", "Content-Type":"application/json", "Accept":"text/html"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer "+os.environ["GITHUB_TOKEN"]
    request = urllib.request.Request("https://api.github.com/markdown", data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        rendered = response.read().decode("utf-8")
    document = RenderedCards()
    document.feed(rendered)
    if document.cards != len(projects):
        raise ValueError("GitHub's rendered output is missing project cards")
    preview = ROOT/".preview"
    preview.mkdir(exist_ok=True)
    (preview/"github-rendered.html").write_text(rendered, encoding="utf-8")
    # Adjust only local resource paths. Preserve native #navigation on this page.
    local = rendered.replace('="assets/', '="../assets/')
    css = """*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#0d1117;color:#e6edf3;font:16px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}.readme{max-width:1012px;margin:32px auto;padding:32px;border:1px solid #30363d;border-radius:6px}p{margin:0 0 16px}h2{font-size:24px;margin:28px 0 16px;padding-bottom:8px;border-bottom:1px solid #30363d}img{max-width:100%;height:auto;vertical-align:middle}a{color:#58a6ff;text-decoration:none}details{margin-bottom:16px}summary{cursor:pointer}sub{color:#a7b2bf}.preview-note{max-width:1012px;margin:20px auto;color:#a7b2bf;font-size:13px}@media(max-width:600px){.readme{margin:12px 8px;padding:16px}.preview-note{margin:12px 24px}}"""
    html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Dipesh Katuwal — portfolio preview</title><style>'+css+'</style></head><body><p class="preview-note">Local preview of GitHub-rendered Markdown. Surrounding GitHub page controls are not included.</p><main class="readme">'+local+'</main></body></html>'
    (preview/"index.html").write_text(html, encoding="utf-8")
    print(f"GitHub Markdown renderer accepted {document.cards} linked project cards and {document.sources} responsive/theme/motion sources.")
    print("Serve the repository with python -m http.server 8765 --bind 127.0.0.1; open http://127.0.0.1:8765/.preview/index.html")


if __name__ == "__main__":
    main()
