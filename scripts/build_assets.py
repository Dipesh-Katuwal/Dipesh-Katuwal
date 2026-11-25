"""Rebuild the complete portfolio from local configuration and verified data."""
from svg_canvas import OUTPUT
from portfolio_sections import (DATA, PROJECTS, WRITTEN, hero, toolkit,
    project_header, project_card, statistics, languages, calendar, recent, footer)
from readme_builder import readme


def main():
    if DATA.get("schema_version") != 2:
        raise ValueError("Run scripts/refresh_data.py first.")
    for mobile in (False, True):
        for static in (False, True):
            hero(mobile, static)
            for light in (False, True):
                calendar(mobile, static, light)
        toolkit(mobile)
        project_header(mobile)
        statistics(mobile)
        languages(mobile)
        recent(mobile)
        footer(mobile)
    for index, project in enumerate(PROJECTS):
        project_card(project, index)
    readme()
    for path in OUTPUT.glob("*.svg"):
        if path.name not in WRITTEN:
            path.unlink()
    print(f"Built README and {len(WRITTEN)} self-contained assets.")


if __name__ == "__main__":
    main()
