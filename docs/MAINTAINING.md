# Maintaining this profile

The README is an image-led portfolio designed for GitHub's constrained renderer. All display assets are stored here; visitors do not depend on public card generators, font CDNs, or live API requests.

## Edit and rebuild

```sh
python -m pip install -r requirements.txt
python scripts/build_assets.py
python scripts/validate_profile.py
```

Edit the four entries in `data/projects.json` to change featured projects. Each includes a source link and an evidence note. Only describe implemented, documented behavior. The hero and visual tokens live in `scripts/build_assets.py`. Font files are bundled to make outlining reproducible on Windows and Linux.

To refresh activity locally:

```sh
python scripts/refresh_data.py
python scripts/build_assets.py --activity-only
python scripts/validate_profile.py --check-links
```

The daily/manual workflow performs these steps and commits the data and four activity SVGs using the built-in `GITHUB_TOKEN`. No personal access token or paid service is required. The workflow becomes available after it is pushed to the default branch. GitHub Actions must be enabled, repository rules must permit the bot's commit, and inactive public repositories may have scheduled workflows disabled by GitHub. Run it manually to re-enable if needed.

## What the numbers mean

- **Contributions:** GitHub's own “contributions in the last year” heading from the public calendar. This is not a count of commits alone. GitHub controls whether anonymized private activity is included in the visible calendar.
- **Active days:** the count of nonzero cells in the displayed grid. GitHub aligns the grid to complete weeks, so this is explicitly a grid statistic.
- **Public repos:** distinct repository links from the public repository listing, including this profile repository and any public forks.
- **Intensity:** GitHub's `data-level` values, mapped to the five blue colors in the generator. No counts or cells are synthesized.

`data/profile.json` records the capture time, source URLs, calendar range, day levels, and repository names. GitHub's unauthenticated API was rate-limited during the initial build, so the refresh reads public HTML instead. Strict parsing checks reject incomplete calendars. If GitHub changes its markup or a fetch fails, the workflow fails before committing and the existing assets remain available. This is a dated snapshot, not a live feed; GitHub's image cache may also delay visible refreshes.

The custom snake is decorative motion along actual active cells in chronological order. It does not represent additional contributions or a score, and does not erase or alter the calendar. This small implementation avoids a second service or action dependency. Reduced-motion sources and a native static-calendar link provide a still alternative.

## Rendering choices

- Hero, project grid, toolkit, footer, and activity have separate desktop/mobile SVGs selected by `<picture>` sources. Mobile project cards are stacked; native project links wrap naturally.
- SVG text is outlined with FontTools for consistent typography. SVG titles/descriptions and README alternatives retain text equivalents. Source fonts and licenses are retained locally.
- Images have intrinsic viewBoxes and use GitHub's normal responsive image sizing. No page CSS, JavaScript, inline SVG, `foreignObject`, external font loads, or interactive SVG links are required.
- The avatar is embedded as JPEG data inside each hero. To replace it, update `assets/avatar.jpg` and rebuild.
- The dark panels intentionally retain their identity in light and dark GitHub themes; GitHub controls the surrounding page and native typography.
- Repository links are native Markdown below the project graphic. An SVG displayed through `<img>` cannot supply reliable per-card links.

## Asset credits

- Manrope by the Manrope Project Authors; SIL Open Font License, see `assets/fonts/Manrope-OFL.txt`.
- JetBrains Mono by the JetBrains Mono Project Authors; SIL Open Font License, see `assets/fonts/JetBrainsMono-OFL.txt`.
- Technology logos from [Devicon](https://github.com/devicons/devicon), MIT; see `assets/icons/DEVICON-LICENSE.txt`. Logos remain trademarks of their owners. SVGs were retrieved from Devicon on 25 November 2026 and stored locally.
- Portrait: the public avatar of [Dipesh-Katuwal](https://github.com/Dipesh-Katuwal).
- Panels, layout, and contribution animation: custom assets for this repository.

For the researched alternatives, see [Platane/snk](https://github.com/Platane/snk), [GitHub Readme Stats](https://github.com/anuraghazra/github-readme-stats), [lowlighter/metrics](https://github.com/lowlighter/metrics), and [GitHub Readme Activity Graph](https://github.com/Ashutosh00710/github-readme-activity-graph).
