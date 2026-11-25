# Maintaining the developer portfolio

The README, project cards, statistics, and calendar are generated from editable configuration and a verified public GitHub snapshot. Visitors load local SVG assets through GitHub; they do not contact a stats-card service, font CDN, or API.

## Change your content

| File | What to edit |
| --- | --- |
| `data/portfolio.json` | Name, role, introduction, typing lines, social/contact links, location, interests, technology groups, optional current work/learning, colors, and language exclusions. |
| `data/projects.json` | Featured repositories, in the order you want them displayed; optional curated titles, descriptions, technology labels, and demo overrides. |
| `data/profile.json` | Generated snapshot. Do not manually change numbers here. |
| `scripts/portfolio_sections.py` | Panel layout and typography sizes. |
| `scripts/readme_builder.py` | Native navigation, links, and image source ordering. |
| `scripts/svg_canvas.py` | Shared SVG primitives and theme mapping. |

A new featured project can be as small as:

```json
{"repository": "CryptoWebsite"}
```

The refresh obtains its actual description, primary language, stars, forks, push date, and homepage. The generator uses those values when no editorial override is supplied. If GitHub has no description, add an accurate `description` in configuration. Use a short `title` and up to three short `technologies` labels for the best layout. Add, remove, or reorder entries; there is no fixed four-card limit. An odd final card remains centered. Cards are real HTML links to source repositories. Demo links are native Markdown beneath them.

Demo discovery checks `demo_url` in project configuration, then the repository homepage, then a README link labeled Live Demo, Demo, or Live Site. Only HTTPS demo links are displayed. A custom `demo_url` should point to an actual deployment documented in your repository. The first build discovered `https://airesumeanalyzer.puter.site/` from the resume analyzer README and verified it returned HTTP 200; its sign-in/application behavior was not audited.

### Personal information

`location`, `currently_working_on`, and `currently_learning` start empty because they were not supplied. Empty optional sections are omitted. Fill these with your own statements. Add social links to the `links` array, for example `{"label":"LinkedIn","url":"https://www.linkedin.com/in/YOUR-HANDLE/"}`, or an email link using `mailto:`. Do not publish an address you do not want public. The current GitHub link is the only configured contact method.

The Project tooling group contains Git, Maven, and Vite: tooling evidenced by your workflow and repositories. Add icons under `assets/icons/` and matching entries under `technology_groups`. Icons indicate tools used, not proficiency. The current layout accommodates up to three items per group. Keep typing lines short enough to fit the mobile hero; the generator truncates an overlong line. Use at least one typing line.

### Colors and portrait

Edit the named hexadecimal tokens in `data/portfolio.json` under `colors`, then rebuild. The calendar also has light variants selected using `prefers-color-scheme`. Other panels intentionally retain the reference's dark visual identity in either GitHub theme. GitHub controls the surrounding page.

Replace `assets/avatar.jpg` with your JPEG portrait to update the hero. It is embedded inside the SVG, so the image does not depend on a separate external avatar request. Bundled Manrope and JetBrains Mono fonts are outlined during generation, which keeps typography consistent without remote font loading.

## Build and verify locally

```sh
python -m pip install -r requirements.txt
python scripts/refresh_data.py
python scripts/build_assets.py
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_profile.py --check-links
```

If you only change layout, colors, or existing editorial text, skip the network refresh and rebuild from the existing snapshot. If you add a repository, run the refresh first. Generated README content should not be edited directly: the next refresh overwrites it. All hand-maintained content belongs in the two configuration files.

To inspect GitHub's official Markdown rendering before publishing:

```sh
python scripts/preview_profile.py
python -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/.preview/index.html`. This renders Markdown through GitHub's API without committing or publishing anything, then uses local images and approximate GitHub spacing. It checks that the sanitizer retained each linked project card. The surrounding native profile interface is outside this preview. `.preview/` is ignored by Git.

The build removes obsolete `.svg` files from `assets/generated/` after a successful build. That directory is exclusively generated output; store original custom assets elsewhere.

## Automated refresh

The daily/manual workflow runs at approximately 06:00 Nepal time and rebuilds the complete README and assets using the repository's built-in `GITHUB_TOKEN`. No personal token, external account, paid service, or public card endpoint is required. It reads public data and commits only the successful snapshot, README, and generated assets. On API, calendar, rendering, or validation failure, nothing is committed and published assets remain intact.

After pushing, enable Actions and use **Actions > Refresh profile activity > Run workflow**. Repository rules must allow the bot's commit. The default branch must contain the workflow. GitHub can delay scheduled runs, and inactive public repositories can have schedules disabled. The refresh uses roughly 20-30 API requests for the current profile, comfortably below the documented 1,000 requests/hour workflow-token allowance.

Local refreshes work without a token while the shared 60 requests/hour unauthenticated allowance is available. If GitHub rate-limits the local IP, keep the existing snapshot or run the authenticated workflow. `GITHUB_TOKEN`, if provided to the script, is only sent to `api.github.com`, never to raw README files, demo sites, or image services. No token is written into the data, README, or images.

## Exact statistic definitions

- **Contributions since joining:** sum of GitHub's visible yearly contribution headings, from account creation year through the current year. This is not a count of commits alone. Private activity can appear anonymously if the owner enables it; hidden contributions are not accessible.
- **Last-year contributions:** GitHub's rolling-calendar heading, kept separate from the historical sum.
- **Active days:** nonzero cells in the displayed grid. The grid aligns to complete weeks and can contain a few days outside exactly 365 days.
- **Current streak:** consecutive active calendar dates ending today or yesterday. An unfinished inactive today does not break yesterday's streak. Calculation is anchored to the UTC capture date.
- **Longest streak:** longest run within the displayed calendar, not a lifetime claim.
- **Public repos:** public repositories owned by the account, including this profile and public forks; checked against the paginated API list.
- **Followers / following:** public user endpoint counts at capture time.
- **Stars received:** sum on original public repositories, excluding forks.
- **Public pull requests / issues:** GitHub Search counts for publicly indexed items authored by this account. These are lifetime indexed counts, not last-year contribution-category counts.
- **Languages:** GitHub language-byte endpoints summed across original public repositories, excluding forks and configured `language_exclusions`. This profile is excluded so generated Python/SVGs do not distort the portfolio. Shares are code composition, not skill levels or hours; GitHub Linguist rules affect classification.
- **Repository updates:** latest `pushed_at` values on public repositories, excluding this profile. These are not claims about what you are currently working on.
- **Public events:** selected records from the latest 100 returned events, filtered to the last 30 days. GitHub documents a maximum 300-event/30-day timeline and delays from 30 seconds to six hours. The feed can omit activity and does not constitute a complete log. The UI never invents commit counts when a PushEvent omits them.

Sources, capture time, calendar dates, yearly totals, repository facts, language bytes, and events are retained in `data/profile.json`. The calendar requires public HTML because a workflow token does not provide a universal public-user GraphQL contribution solution. Strict parsing rejects incomplete or changed calendar markup; adjust the parser when GitHub changes its HTML.

## Rendering and accessibility

Project images have fixed preferred widths and wrap naturally into one column when two cards cannot fit. At typical wide profile widths they appear in two columns. The mobile calendar splits the year into two chronological bands to keep cells and month labels readable. Static hero/calendar sources are selected for reduced-motion preferences, and a native static-calendar link is always available. The snake is decorative motion through actual active cells; it does not create contributions, score activity, or modify the calendar.

Every image has alternative text, and the native Markdown provides navigation, repository/demo links, contribution-year links, contact links, and expandable text equivalents for projects and activity. Native GitHub typography remains under GitHub's control. No page CSS, browser JavaScript, inline SVG, external SVG resources, or `foreignObject` is needed.

Validation checks image references, linked cards, native navigation, XML structure, SVG references and unique IDs, motion/theme sources, calendar continuity, streaks, yearly sums, and language exclusions. The data tests cover today/yesterday streak handling, stale calendars, malformed grids, missing event counts, and retaining the last snapshot after a failed fetch.

## Native GitHub sections

The README cannot remove GitHub's sidebar, native repository area, contribution calendar, or activity timeline. **Customize your pins** lets you choose and reorder up to six repositories/gists; removing all pins can restore Popular repositories. Contribution settings let you adjust the activity overview and visibility of anonymized private activity. Profile settings also let you control achievement visibility. These settings do not turn the README into a replacement for GitHub's page layout. Keep native pins aligned with your curated list if you want consistency; this project does not change account settings.

## Credits

- Manrope and JetBrains Mono: SIL Open Font License; license files are in `assets/fonts/`.
- Technology logos: [Devicon](https://github.com/devicons/devicon), MIT; see `assets/icons/DEVICON-LICENSE.txt`. Logos remain trademarks of their owners.
- Portrait: the public avatar of [Dipesh-Katuwal](https://github.com/Dipesh-Katuwal).
- Panel system, layouts, typing animation, and contribution trail: custom assets for this portfolio.

See `docs/DESIGN.md` for the audit, service decisions, and verification scope.
