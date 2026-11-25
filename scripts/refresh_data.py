"""Refresh public GitHub facts. A failed fetch leaves the previous snapshot intact."""
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = "Dipesh-Katuwal"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Dipesh-Katuwal-profile/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "td" and "data-date" in attrs and "data-level" in attrs:
            self.days.append({"date": attrs["data-date"], "level": int(attrs["data-level"])})


def main():
    calendar_url = f"https://github.com/users/{USER}/contributions"
    repositories_url = f"https://github.com/{USER}?tab=repositories"
    calendar = fetch(calendar_url)
    parser = CalendarParser()
    parser.feed(calendar)
    total = re.search(r'id="js-contribution-activity-description"[^>]*>\s*([\d,]+)\s+contributions?', calendar)
    if not total:
        raise ValueError("GitHub contribution heading changed; keeping the last snapshot.")
    days = sorted(parser.days, key=lambda day: day["date"])
    if not 350 <= len(days) <= 378 or len({d["date"] for d in days}) != len(days):
        raise ValueError("Incomplete or duplicate calendar; keeping the last snapshot.")
    if any(day["level"] not in range(5) for day in days):
        raise ValueError("Unexpected contribution intensity.")
    for day in days:
        date.fromisoformat(day["date"])
    # Count the actual repository links, following pagination when necessary.
    repositories = set()
    for page in range(1, 101):
        url = repositories_url if page == 1 else repositories_url + f"&page={page}"
        listing = fetch(url)
        found = set(re.findall(r'<a\s+href="/' + USER + r'/([^"/]+)"\s+itemprop="name codeRepository"', listing))
        if not found or found <= repositories:
            break
        repositories |= found
        if not re.search(r'rel="next"|class="next_page"', listing):
            break
    if not repositories:
        raise ValueError("Repository listing unavailable; keeping the last snapshot.")
    snapshot = {
        "username": USER,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "contributions_last_year": int(total.group(1).replace(",", "")),
        "active_days_in_grid": sum(day["level"] > 0 for day in days),
        "public_repositories": len(repositories),
        "repositories": sorted(repositories),
        "calendar_start": days[0]["date"],
        "calendar_end": days[-1]["date"],
        "sources": [calendar_url, repositories_url],
        "days": days,
    }
    target = ROOT / "data/profile.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(f"Updated: {snapshot['contributions_last_year']} contributions; {len(repositories)} public repositories.")


if __name__ == "__main__":
    main()
