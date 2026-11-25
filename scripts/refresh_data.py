"""Fetch a complete public snapshot; failed refreshes never replace the last success."""
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote
import json
import os
import re
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / "data/portfolio.json").read_text(encoding="utf-8"))
USER = SETTINGS["username"]
API = "https://api.github.com"


def fetch(url, api=False):
    headers = {"User-Agent": f"{USER}-portfolio/2.0"}
    if api:
        if not url.startswith(API + "/"):
            raise ValueError("API token may only be sent to api.github.com")
        headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        if os.environ.get("GITHUB_TOKEN"):
            headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub refresh failed: HTTP {error.code} for {url}. Previous snapshot retained.") from None
    return json.loads(text) if api else text


def api(path):
    return fetch(API + path, api=True)


def paginate(path):
    records = []
    for page in range(1, 101):
        separator = "&" if "?" in path else "?"
        batch = api(f"{path}{separator}per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("GitHub did not return a paginated list")
        records.extend(batch)
        if len(batch) < 100:
            return records
    raise ValueError("Pagination exceeded the safety bound")


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "td" and "data-date" in attrs and "data-level" in attrs:
            self.days.append({"date": attrs["data-date"], "level": int(attrs["data-level"])})


def parse_calendar(html, full_grid=True):
    heading = re.search(r'id="js-contribution-activity-description"[^>]*>\s*([\d,]+)\s+contributions?', html)
    if not heading:
        raise ValueError("GitHub contribution markup changed; previous snapshot retained")
    parser = CalendarParser()
    parser.feed(html)
    days = sorted(parser.days, key=lambda day: day["date"])
    if not days or len({d["date"] for d in days}) != len(days):
        raise ValueError("Missing or duplicate contribution days")
    if full_grid and not 350 <= len(days) <= 378:
        raise ValueError("Incomplete contribution calendar")
    for index, day in enumerate(days):
        date.fromisoformat(day["date"])
        if day["level"] not in range(5):
            raise ValueError("Invalid calendar intensity")
        if index and (date.fromisoformat(day["date"]) - date.fromisoformat(days[index-1]["date"])).days != 1:
            raise ValueError("Contribution calendar has gaps")
    return int(heading.group(1).replace(",", "")), days


def streaks(days, today):
    visible = [d for d in days if date.fromisoformat(d["date"]) <= today]
    longest = run = 0
    for day in visible:
        run = run + 1 if day["level"] > 0 else 0
        longest = max(longest, run)
    # Anchor at today or yesterday; a stale calendar cannot imply an active streak.
    by_date = {day["date"]: day["level"] for day in visible}
    cursor = today if by_date.get(today.isoformat(), 0) > 0 else today-timedelta(days=1)
    current = 0
    while by_date.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    return {"current": current, "longest_in_grid": longest, "as_of": today.isoformat(), "timezone": "UTC"}


def normalize_event(event):
    kind = event["type"]
    payload = event.get("payload", {})
    repo = event["repo"]["name"]
    base = "https://github.com/" + repo
    result = {"type": kind, "repository": repo, "created_at": event["created_at"], "url": base}
    if kind == "PushEvent":
        result["summary"] = "Pushed to " + payload.get("ref", "refs/heads/main").removeprefix("refs/heads/")
        if payload.get("head"):
            result["url"] = base + "/commit/" + payload["head"]
    elif kind in {"PullRequestEvent", "IssuesEvent"}:
        item = payload.get("pull_request" if kind == "PullRequestEvent" else "issue", {})
        result["summary"] = payload.get("action", "Updated").capitalize() + (" pull request" if kind == "PullRequestEvent" else " issue") + (f" #{item['number']}" if item.get("number") else "")
        result["url"] = item.get("html_url", base)
    elif kind == "CreateEvent":
        result["summary"] = "Created " + payload.get("ref_type", "repository")
    elif kind == "ReleaseEvent":
        result["summary"] = "Published release"
        result["url"] = payload.get("release", {}).get("html_url", base + "/releases")
    elif kind == "WatchEvent":
        result["summary"] = "Starred repository"
    elif kind == "ForkEvent":
        result["summary"] = "Forked repository"
    else:
        return None
    return result


def find_demo(repo, configured):
    if configured.get("demo_url"):
        return configured["demo_url"], "configuration (verified repository README)"
    homepage = (repo.get("homepage") or "").strip()
    if homepage.startswith("https://"):
        return homepage, "repository homepage"
    # Only read this public repository's own README; do not follow arbitrary links.
    raw = f"https://raw.githubusercontent.com/{USER}/{repo['name']}/{quote(repo['default_branch'], safe='')}/README.md"
    try:
        text = fetch(raw)
    except (RuntimeError, urllib.error.URLError):
        return None, None
    match = re.search(r'\[(?:Live Demo|Demo|Live Site)\]\((https://[^\s)]+)\)', text, re.I)
    return (match.group(1), raw) if match else (None, None)


def main():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    today = now.date()
    user = api(f"/users/{USER}")
    repos = paginate(f"/users/{USER}/repos?type=owner&sort=pushed")
    if len(repos) != user["public_repos"]:
        raise ValueError("Public repository listing is incomplete; keeping previous data")
    sources = [f"{API}/users/{USER}", f"{API}/users/{USER}/repos"]
    calendar_url = f"https://github.com/users/{USER}/contributions"
    annual, days = parse_calendar(fetch(calendar_url))
    sources.append(calendar_url)
    years = []
    joined = int(user["created_at"][:4])
    for year in range(joined, today.year + 1):
        end = min(today, date(year, 12, 31))
        url = f"{calendar_url}?from={year}-01-01&to={end.isoformat()}"
        count, _ = parse_calendar(fetch(url), full_grid=False)
        years.append({"year": year, "contributions": count, "source": url})
    # Repository statistics are snapshots. Exclude forks and generated profile code
    # from language totals, while including all public owned repos in the repo count.
    totals = {}
    language_repos = []
    for repo in repos:
        if repo["fork"] or repo["name"] in SETTINGS["language_exclusions"]:
            continue
        languages = api(f"/repos/{USER}/{repo['name']}/languages")
        if not isinstance(languages, dict) or any(not isinstance(n, int) or n < 0 for n in languages.values()):
            raise ValueError("Invalid language byte counts")
        language_repos.append(repo["name"])
        for language, size in languages.items():
            totals[language] = totals.get(language, 0) + size
    by_name = {repo["name"]: repo for repo in repos}
    configured = json.loads((ROOT / "data/projects.json").read_text(encoding="utf-8"))
    featured = {}
    for item in configured:
        if item["repository"] not in by_name:
            raise ValueError(f"Featured repository is not public: {item['repository']}")
        repo = by_name[item["repository"]]
        demo, demo_source = find_demo(repo, item)
        featured[repo["name"]] = {
            "name": repo["name"], "description": repo.get("description"),
            "url": repo["html_url"], "language": repo.get("language"),
            "stars": repo["stargazers_count"], "forks": repo["forks_count"],
            "pushed_at": repo["pushed_at"], "archived": repo["archived"],
            "demo_url": demo, "demo_source": demo_source,
        }
    events_url = f"/users/{USER}/events/public?per_page=100"
    events = api(events_url)
    if not isinstance(events, list):
        raise ValueError("Invalid activity feed")
    normalized = [entry for event in events if (entry := normalize_event(event))]
    recent = [event for event in normalized if now - timedelta(days=30) <= datetime.fromisoformat(event["created_at"].replace("Z", "+00:00")) <= now]
    recent.sort(key=lambda event: event["created_at"], reverse=True)
    issue_counts = {}
    for kind in ("issue", "pr"):
        result = api("/search/issues?q=" + quote(f"author:{USER} is:{kind} is:public", safe="") + "&per_page=1")
        if result.get("incomplete_results"):
            raise ValueError("Incomplete issue search results")
        issue_counts[kind] = result["total_count"]
    snapshot = {
        "schema_version": 2, "username": USER, "updated_at": now.isoformat(),
        "contributions_last_year": annual,
        "contributions_since_joining": sum(year["contributions"] for year in years),
        "contributions_by_year": years, "joined_year": joined,
        "active_days_in_grid": sum(day["level"] > 0 for day in days),
        "public_repositories": user["public_repos"], "repositories": sorted(by_name),
        "followers": user["followers"], "following": user["following"],
        "stars_on_original_repos": sum(repo["stargazers_count"] for repo in repos if not repo["fork"]),
        "public_pull_requests": issue_counts["pr"], "public_issues": issue_counts["issue"],
        "streak": streaks(days, today),
        "languages": dict(sorted(totals.items(), key=lambda item: (-item[1], item[0]))),
        "language_repositories": language_repos,
        "featured": featured,
        "recent_updates": [{"repository": repo["name"], "url": repo["html_url"], "pushed_at": repo["pushed_at"], "language": repo.get("language")} for repo in sorted(repos, key=lambda repo: repo["pushed_at"], reverse=True) if repo["name"] != USER][:3],
        "recent_events": recent[:4],
        "events_returned_in_30_days": len(recent),
        "calendar_start": days[0]["date"], "calendar_end": days[-1]["date"],
        "sources": sources + [API + events_url, f"{API}/repos/{{owner}}/{{repo}}/languages", f"{API}/search/issues"],
        "days": days,
    }
    target = ROOT / "data/profile.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(f"Verified snapshot: {annual} contributions in the last year; {snapshot['contributions_since_joining']} since joining; {len(repos)} public repositories.")


if __name__ == "__main__":
    main()
