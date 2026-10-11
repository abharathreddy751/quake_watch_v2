# QuakeWatch design system — "Seismic Intelligence"

Bootstrap 5.3 (vendored) plus one token layer in `static/qw/css/qw.css`. The visual language
borrows from seismology instruments and survey maps: topographic contours, seismograms,
wavefronts radiating from an epicentre, mono coordinate read-outs. Pages never hard-code colours
or spacing; they use these tokens, the `qw-*` components or Bootstrap utilities (Bootstrap's own
variables are re-pointed at the tokens, so stock alerts, badges, forms, tables, tabs, dropdowns and
pagination follow the theme). The CSP forbids inline styles, so all styling lives in `qw.css`.

**Themes.** Dark is the primary theme and the default on first visit; the toggle switches to the
light theme and the choice is remembered in `localStorage` (`qw-theme`). The pre-paint script in
`base.html` applies it before first render. Both themes use the same token names.

## Tokens

| Group | Tokens | Notes |
|---|---|---|
| Typography | `--qw-font-sans` (Inter, self-hosted), `--qw-font-mono` (JetBrains Mono), `--qw-text-2xs … --qw-text-display` | 1.2 scale; mono for coordinates, times, ids, metric labels; tabular figures on numbers |
| Spacing | `--qw-space-1 … --qw-space-12` | 4 px grid |
| Shape | `--qw-radius-xs/sm/-/lg/pill` | |
| Surfaces | `--qw-bg`, `--qw-bg-2`, `--qw-surface`, `--qw-surface-alt`, `--qw-surface-raised`, `--qw-input-bg`, `--qw-border`, `--qw-border-strong`, `--qw-hairline` | dark: `#0B0F14 / #111821 / #17212B / #1C2733` |
| Text | `--qw-text`, `--qw-text-2`, `--qw-text-muted`, `--qw-text-faint` | `faint` only for decoration/placeholder |
| Accent | `--qw-accent` (`#FF7548` dark / `#B83D0B` light), `--qw-on-accent`, `--qw-link`, `--qw-focus` | actions, selection, focal elements |
| Severity | `--qw-highlight` (`#FF4D4F`) | genuinely severe states only, so red keeps its meaning |
| Geology | `--qw-gold` (`#F5B942`) | secondary accent |
| Status | `--qw-ok`, `--qw-info`, `--qw-warn`, `--qw-danger`, `--qw-fresh/degraded/stale/unknown` | always paired with a text label |
| Tints | `--qw-tint-{success,danger,warning,info,neutral,accent}{,-bg,-bd}` | badges and alerts: text ≥ 4.5:1 on its tint |
| Magnitude | `--qw-mag-0 … 4`, `--qw-mag-ink-0 … 4` | ordinal ramp, below |
| Charts | `--qw-series-1` (orange: counts, magnitude), `--qw-series-2` (blue: depth), `--qw-series-muted`, `--qw-chart-grid`, `--qw-chart-text` | |
| Map | `--qw-marker-stroke`, `--qw-map-bg`, `--qw-tile-filter` | dark theme re-tints OSM tiles with a CSS filter |
| Motion | `--qw-dur-1` 120 ms (hover/press), `--qw-dur-2` 200 ms (menus, tabs, reveals), `--qw-dur-3` 320 ms (overlays), `--qw-ease` | |
| Elevation | `--qw-shadow-1/2`, `--qw-glow`, `--qw-z-*` | |
| Focus | `--qw-focus-ring` | two-tone ring (background gap + solid accent) on every `:focus-visible`, ≥ 3:1 |

Every text/background pair was checked with a contrast script (WCAG 2.2 AA: 4.5:1 text, 3:1 focus
ring) in both themes before shipping; the axe suite re-checks the rendered pages.

### Magnitude ramp

Bands (< 2.5, 2.5–4.5, 4.5–6, 6–7, ≥ 7) are **ordered**, so they use one warm hue from light to
dark: gold → amber → orange → red → crimson. Each theme's ramp has monotone OKLab lightness with
steps ≥ 0.06, and every step clears 2:1 against the panel surface. Badge text colours
(`--qw-mag-ink-*`) meet 4.5:1 on every step. Magnitude is never encoded by colour alone: markers
also scale in size, and every badge shows the number.

| Band | Dark | Light |
|---|---|---|
| < 2.5 | `#FFD166` | `#E8A33A` |
| 2.5–4.5 | `#FFA24C` | `#E0712C` |
| 4.5–6 | `#FF7548` | `#C9432A` |
| 6–7 | `#F2464B` | `#962430` |
| ≥ 7 | `#D42F6A` | `#5E1538` |

Chart datasets record the token they were coloured from (`qwToken`) and map markers are restyled
on the `qw:theme` event, so switching theme recolours them with that theme's steps.

## Brand

`templates/partials/mark.html` is the mark: concentric wavefronts around an epicentre, crossed by
a seismogram (inline SVG, themed by CSS). `static/qw/img/mark.svg` is the favicon variant.
`static/qw/img/topo.svg` holds generated topographic contours used as a faint page backdrop, the
dashboard hero, the auth brand panel and nothing else.

## Components

| Component | Class / helper | Contract |
|---|---|---|
| Page header | `.qw-page-header` + `.qw-eyebrow` | eyebrow label, one `h1`, one-line purpose; accent "fault offset" on the divider |
| Hero | `.qw-hero`, `.qw-seismo` | dashboard only; the seismogram is decorative (`aria-hidden`, labelled "Illustrative") |
| Panel | `.qw-card`, `.qw-card-head`, `.qw-panel-title`, `.qw-card--grid`, `.qw-card--map` | direct `h2/h3` get an accent tick; equal height only when alone in a grid column |
| Metric | `.qw-metric` (`__label`, `__value`, `__note`, `data-tone`), `.qw-metric--feature` | real API values only; the tone tick is decorative |
| Stat tile | `.qw-stat`, `.qw-stat-label` | number + label |
| Event console list | `.qw-event-list` > `.qw-event[data-band]` | severity tick + magnitude badge + place + mono metadata |
| Magnitude badge | `QW.magBadge()` / `.qw-mag[data-band]` | screen-reader prefix "Magnitude" |
| Magnitude dial | `.qw-mag-dial[data-band]` | event detail header (decorative; the value is in the title and source values) |
| Epicentre glyph | `.qw-epicentre` (`--static`, `--severe`) | pulses only for M4.5+ (same rule as the map halos) |
| Freshness | `[data-qw-freshness]` | dot + status word + time; only a live feed pulses; polls every 60 s |
| Filter chips | `.qw-chips` > `.qw-chip` | one removable chip per active Explorer filter (24 px remove target) |
| Key–value | `.qw-kv` (`<dl>`) | source vs derived values in separate lists |
| Table | `.qw-table` in `QW.scrollRegion(label, table)` | mono uppercase heads, numeric columns right-aligned with tabular figures, sortable headers are buttons with `aria-sort` and ↕/▲/▼ indicators |
| Chart | `QWCharts.figure()` / `.bar({token})` | canvas `role="img"` + summary caption + "Show data table"; tooltips/grid from tokens |
| Map | `QWMap.create()` / `.eventLayer()` / `.busy()` / `.selectRing()` | survey-frame corners, legend (incl. halo key), cursor coordinates; pulse halo for M4.5+ in the last 24 h; reticle for the selected event; the page always has an equivalent text list |
| Timeline | `.qw-timeline` | ordered list, newest first |
| Form field | `partials/field.html` | label↔input, required marker, `aria-describedby` for help and errors |
| Auth layout | `.qw-auth`, `partials/auth_brand.html` | brand panel hidden below `lg` |

## Seismic loader

`QW.loader(label, {size})` renders the QuakeWatch loader: an epicentre emitting three wavefronts
(accent, red, gold), pure CSS. Sizes: `sm` (inline, buttons, status lines), `md` (data regions),
`lg` (map overlay via `QWMap.busy`). It always sits inside a `role="status"` region with a text label
("Loading earthquake data…"). `QW.busy(button, on)` disables a button and shows the small loader
while a request runs. With `prefers-reduced-motion` the wavefronts are drawn as static rings.

## UI states (every data region)

`QW.load(el, path, render, opts)` renders exactly one of the states below (`opts.loading` sets the
loading label). Code that sets a loading state by hand must finish with `QW.fill(el, …)` (or
`QW.errorState`), which also ends the region's `aria-busy` period. New content fades in (`.qw-reveal`).

| State | Trigger | Presentation |
|---|---|---|
| Loading | request in flight | seismic loader + label, skeleton rows that reserve the content's space, `aria-busy` |
| Success | 2xx with data | `render()` output |
| Empty | `render()` returns `false` | inbox icon + page-specific guidance |
| Partial | page-specific (for example, clustered map, truncated table) | inline warning notice |
| Validation error | 400 | message + per-field list; forms mark fields `aria-invalid` and focus the first |
| Auth required | 401, or 403 while signed out | "Please log in" + login link with `next` |
| Permission error | 403 while signed in | lock icon + message |
| Not found | 404 | message from the API |
| Throttled | 429 | wait message + retry |
| Server failure | 5xx | fixed public message, retry button, correlation id |
| Network failure | fetch rejected | connection message + retry |

Full-page errors use `templates/400|403|404|503.html` (error code, static epicentre, next steps)
and a standalone `500.html` that needs no context processors.

## Motion

Small, consistent and purposeful: page content enters in 240 ms (no cross-document view
transitions: Chromium aborts them on POST→redirect navigations such as log in and reports a page
error); menus, tabs and chips use 200 ms; data regions fade
in when content arrives. Earthquake-specific motion is limited to: the loader, the hero seismogram
(one 9 s recording loop), the live-feed dot, the strongest-event epicentre (M4.5+ only), map halos
(at most 12, M4.5+ in the last 24 h) and the selection reticle. Nothing shakes or flashes.
`prefers-reduced-motion` disables all of it (static rings, full static trace, no entrance animation).

## Accessibility checklist (WCAG 2.2 AA)

Audited automatically and manually; findings, fixes and exceptions are in [ACCESSIBILITY.md](ACCESSIBILITY.md).

- Skip link to `#main`; landmarks (`header/nav`, `main`, `aside`, `footer`); one `h1` per page, sequential headings.
- All controls are native elements (buttons, links, inputs); icon-only buttons have `aria-label`.
- Live regions: `#qw-live` for announcements (sort changes, saves, deletions, filter removal); map/result status lines use `role="status"`.
- Charts: summary sentence as the accessible name and caption, plus a data table.
- Maps: text list of the same events (Live Map side panel, Explorer table, Dashboard recent list); decorative map overlays (halos, reticle, coordinates, loading overlay) are hidden from assistive technology.
- `prefers-reduced-motion` disables animations (loader, skeleton shimmer, seismogram, pulses, page entrance, Chart.js animation).
- Colour is never the only carrier of meaning (magnitude, freshness, status badges all have text).
- Responsive down to 320 px (tested): navigation collapses below `xl`; tables scroll horizontally inside a focusable region.
- Targets are at least 24 px (pager buttons 32 px; chip remove buttons 24 px; link lists 28 px rows); map markers use 2.5.8's equivalent-control exception.
