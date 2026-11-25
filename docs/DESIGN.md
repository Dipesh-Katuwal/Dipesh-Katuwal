# Portfolio expansion: audit and implementation decisions

## Initial audit

The original README contained an intentional hero, a six-icon technology strip, a single-image four-project grid, three activity numbers, a decorative contribution trail, and a closing GitHub link. It contained no default "Hi there" placeholder. The extra content below it was GitHub's native interface, which a README cannot hide.

The strongest existing elements were retained: dark surfaces, thin blue borders, rounded cards, Manrope display type, JetBrains Mono metadata, and blue/green/violet lighting. Missing functionality was added around that system: individually linked project cards, documented demo links, grouped tooling, follower/following data, visible historical contribution totals, streaks, languages, yearly history links, and a public activity feed.

## Sources and reliability research

Research and initial snapshot: 25 November 2026.

- [GitHub REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api): 60/hour for unauthenticated shared-IP traffic, 1,000/hour/repository for the workflow token. Use the built-in token during scheduled refreshes; visitors only load stored assets.
- [GitHub Events API](https://docs.github.com/en/rest/activity/events): at most 300 timeline events, limited to 30 days, with possible 30-second to six-hour delays. Show a dated, explicitly limited feed and use repository push dates alongside it.
- [Native pin customization](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/pinning-items-to-your-profile): up to six repositories/gists can be selected and reordered. There is no README technique to hide the native page.
- [GitHub Readme Stats](https://github.com/anuraghazra/github-readme-stats): its shared endpoint is documented as best-effort. Direct GitHub data and local assets avoid that extra runtime dependency.
- [GitHub Readme Activity Graph](https://github.com/Ashutosh00710/github-readme-activity-graph): another shared rate-limited endpoint; not needed when the repository can render its own calendar.
- [Platane/snk](https://github.com/Platane/snk): a good open-source animation generator. The existing custom trail was retained and refined to avoid a second action, authentication path, and visual system. It follows real active cells without pretending to add or consume activity.
- [Devicon](https://github.com/devicons/devicon): local MIT-licensed SVGs. IDs are namespaced when composited to prevent gradient collisions.

The refresh uses official public REST endpoints for user data, paginated repositories, language bytes, issue/PR search counts, and events. The visible public contribution HTML supplies the rolling calendar and yearly contribution headings. The latter is the least stable interface, so incomplete calendars and changed markup fail closed, leaving the published snapshot available.

## Content choices

Featured projects include BillingSoftware, AiResumeAnalyzer, DarazClone, EMS, and Projects_in_C. Descriptions were checked against their public READMEs and selected dependencies. DarazClone uses H2 and is presented as a practice project with a cart UI, not a production payment system. The AI resume analyzer uses Puter and analyzes the first PDF page; no separate custom backend is claimed. GitHub reports its primary repository language as JavaScript while the curated technology labels also correctly include TypeScript.

The owner subsequently confirmed C++ knowledge, so C and C++ are both shown in the toolkit. The C collection was checked against its public README and added as a fifth featured project. Technology groups wrap into additional rows as they grow.

No experience, achievements, trophies, job availability, location, social identity, or current-learning claim was invented. Optional profile fields remain empty until the owner supplies them.

## Verification scope

- The existing published profile HTML was inspected: GitHub preserved the previous responsive and reduced-motion picture sources.
- The expanded README was submitted to GitHub's official `/markdown` renderer and returned HTTP 200. The response preserved all four repository-linked cards and the mobile/theme/motion sources. Its sanitized HTML was saved locally under `.preview/` for inspection.
- All README HTTPS links, including the discovered resume-analyzer demo and linked public activity commits, returned HTTP 200 during validation. A successful demo response is not an application functionality audit.
- All generated SVG variants were rasterized, and desktop/mobile sheets plus the light calendar were visually reviewed. Data calculations and malformed/failed data cases have focused tests.
- Native GitHub page controls are not part of the generated design. The expanded files must be pushed before the live profile can display this revision; local/API preview validation does not claim an unpublished revision is already deployed.

## File structure

`data/portfolio.json` and `data/projects.json` are the editorial inputs. `scripts/refresh_data.py` writes the verified snapshot. The shared canvas, section renderers, and README builder generate the display files. A daily/manual workflow fetches, builds, tests, validates, and commits only after every required step succeeds.

## C/C++ expansion verification

The shared unauthenticated API quota was exhausted during this update. The existing complete statistics snapshot was retained. The C card's description, language, stars, and forks were verified through the public repository HTML; its date was taken from the public repository listing and labeled Updated rather than Pushed. That card records its own metadata source and capture time. The authenticated scheduled refresh replaces it with the normal API snapshot. Five linked cards and all 29 SVGs passed validation; the expanded desktop/mobile toolkit and C card were rendered and visually inspected.
