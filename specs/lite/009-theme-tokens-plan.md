# Plan 009 - Theme tokens (CSS variables)

Date: 2026-05-09

Extend `:root` design tokens in `frontend/src/index.css` to a complete system (spacing scale, radii scale, shadow scale, additional semantic colors), then sweep every `*.module.css` to reference tokens instead of hardcoded `rem`/`px`/hex values. Color tokens already exist; this plan finishes the job and produces a single source of truth that future dark/light themes and design-system audits can target.

## Requirements

### R1 - Complete token taxonomy in `index.css`

`:root` exposes a closed set of design tokens covering spacing, radii, shadows, colors, typography, transitions. No new categories required to style any current view.

* Spacing scale `--space-0` (0) through `--space-8` (3rem) using a consistent step (0.25, 0.375, 0.5, 0.75, 1, 1.25, 1.5, 2, 3rem). Outlier values in modules (0.1, 0.15, 0.2, 0.6875, 0.9375, etc.) snap to the nearest scale step; document the snap map in the plan PR.
* Radius scale `--radius-none` (0), `--radius-sm` (2px), `--radius-md` (4px), `--radius-lg` (8px), `--radius-pill` (999px). Existing `--radius` aliased to `--radius-none` for backwards compatibility, then removed once sweep finishes.
* Shadow scale `--shadow-none`, `--shadow-card` (the existing `0 4px 24px rgba(0,0,0,0.5)` modal shadow), `--shadow-focus` (the existing `inset 0 -1px 0 var(--accent-green-dim)` input underline). Inset error shadow becomes `--shadow-focus-error`.
* New semantic color slots filling current gaps surfaced by the sweep: `--accent-purple` (replaces stray `#aa78ff`), `--accent-blue` (replaces stray `#3b82f6` fallback), `--bg-modal-overlay` (replaces inline `rgba(0,0,0,0.7)` if any).
* Transition tokens `--transition-fast` (`150ms ease`), `--transition-default` (`200ms ease`) — replace the `transition: ... 0.2s` magic numbers already scattered through modules.

### R2 - Every `*.module.css` references tokens, not literals

After sweep, no `*.module.css` in `frontend/src/` contains a raw hex color, raw `rgba()`, raw `box-shadow` value, or raw `rem`/`px` spacing on margin/padding/gap properties. Width/height/`max-width` layout caps (e.g., `max-width: 1200px`, fixed icon sizes) are exempt — tokenizing layout breakpoints is out of scope for this plan.

* Sweep target: 34 module CSS files under `frontend/src/components/` and `frontend/src/pages/`.
* Each margin/padding/gap value resolves to `var(--space-*)` from the scale.
* Each `border-radius` resolves to `var(--radius-*)`.
* Each `box-shadow` resolves to `var(--shadow-*)`.
* Each color (`color`, `background-color`, `border-color`) resolves to an existing or newly-added token in R1. No literals remain.
* Each `transition` duration uses a transition token (the easing/property part stays inline).
* `index.css` global rules (body, button, input) updated in the same sweep for consistency.

### R3 - No visual regression

Sweep is mechanical; final rendered UI matches pre-sweep within 1px tolerance for spacing snaps. Snap deltas (where 0.1/0.6875/0.9375 etc. round to scale steps) are accepted and documented.

* `make check` (root) green: lint + typecheck + vitest + backend pytest.
* Manual smoke: every page (home, resumes, applications, accomplishments, notes, contacts) loads and renders identically at 1280px desktop and 375px mobile breakpoints.
* Visual diff: take before/after screenshots of one representative list page and one detail page; attach to PR. Differences should only be the documented snap deltas.
* Bundle size unchanged within ±0.5 KB gzip (CSS vars are compile-time-free).

### R4 - Token discoverability

Tokens are documented inline so the next contributor doesn't need to read this plan to use them.

* `index.css` `:root` block grouped by category (Spacing, Radii, Shadows, Colors, Typography, Transitions) with one-line section comments.
* Each token group ordered small → large for the scales.
* `frontend/AGENTS.md` (or new `frontend/src/index.css` header comment) gains a 5-line "use tokens, not literals" note pointing at this plan.

## Design

### Spacing scale (snap map)

| Token | Value | Snaps from |
|-------|-------|------------|
| `--space-0` | 0 | 0 |
| `--space-1` | 0.25rem | 0.1, 0.125, 0.15, 0.2, 0.25, 0.3 |
| `--space-2` | 0.375rem | 0.35, 0.375, 0.4, 0.45 |
| `--space-3` | 0.5rem | 0.5 |
| `--space-4` | 0.75rem | 0.625, 0.675, 0.6875, 0.7, 0.75, 0.8 |
| `--space-5` | 0.875rem | 0.8125, 0.875, 0.9, 0.9375, 0.95 |
| `--space-6` | 1rem | 1, 1.05, 1.1, 1.125 |
| `--space-7` | 1.25rem | 1.25, 1.375 |
| `--space-8` | 1.5rem | 1.5 |
| `--space-9` | 2rem | 1.75, 1.875, 2 |
| `--space-10` | 3rem | 3 |

Eleven steps cover 99% of observed values; outliers >3rem (1200px caps etc.) are layout, not spacing — leave as literals.

### Token block sketch (final `:root`)

```css
:root {
  /* Spacing — 11-step scale, mobile-first */
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.375rem;
  --space-3: 0.5rem;
  --space-4: 0.75rem;
  --space-5: 0.875rem;
  --space-6: 1rem;
  --space-7: 1.25rem;
  --space-8: 1.5rem;
  --space-9: 2rem;
  --space-10: 3rem;

  /* Radii */
  --radius-none: 0;
  --radius-sm: 2px;
  --radius-md: 4px;
  --radius-lg: 8px;
  --radius-pill: 999px;

  /* Shadows */
  --shadow-none: none;
  --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.5);
  --shadow-focus: inset 0 -1px 0 var(--accent-green-dim);
  --shadow-focus-error: inset 0 -1px 0 var(--status-error);

  /* Colors — existing tokens preserved + gaps filled */
  /* ...existing bg/text/accent/status... */
  --accent-purple: #aa78ff;
  --accent-blue: #3b82f6;
  --bg-modal-overlay: rgba(0, 0, 0, 0.7);

  /* Typography */
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', ui-monospace, monospace;

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-default: 200ms ease;
}
```

### Sweep mechanics

One pass per module file. Use a small Node/`sed` script (or by hand — 34 files is tractable) to:

1. Replace literal `rem` spacing values per the snap map.
2. Replace `border-radius: 0` → `var(--radius-none)`, `4px` → `var(--radius-md)`, etc.
3. Replace `box-shadow` literals with the shadow tokens.
4. Replace stray hex/rgba() with color tokens (add a token if no good match exists; flag in PR).
5. Replace `0.2s` / `0.15s` durations in `transition` with token references.

Run `npm run lint && npm run test` after each batch of ~5 files — fast feedback if a regex misfires.

### Future work (out of scope)

* Dark/light theme toggle: token names are already neutral (`--bg-primary`, not `--white`), so swapping a `[data-theme="light"]` block in `index.css` becomes mechanical — but the toggle UI + persisted preference is its own plan.
* Stylelint rule enforcing "no literal hex / rem in module CSS" — defer; the sweep + PR review catches drift for now.
* Storybook token gallery — defer to R012.

### Risks

* **Snap deltas visible**: 0.6875rem → 0.75rem is ~1px; spot-check tight layouts (TagInput chips, Breadcrumb) at 375px mobile.
* **Find/replace overshoot**: regex matching `0.5rem` could hit non-spacing properties (e.g., `font-size`). Restrict regex to `margin*`, `padding*`, `gap`, `top|right|bottom|left` properties.
* **Stray literals in third-party overrides**: Clerk component overrides may need their own `--clerk-*` token mapping — already handled in current `index.css`, just verify no new ones leak in.

## Tasks

### P1 - Token definitions

Land tokens in `index.css` first; sweep happens against a stable target.

- [x] T01 Add spacing scale (`--space-0` … `--space-10`) to `:root` in `frontend/src/index.css` per R1 / Design.
- [x] T02 Add radius scale (`--radius-none/sm/md/lg/pill`); alias existing `--radius` → `--radius-none` for one transition commit.
- [x] T03 Add shadow scale (`--shadow-none/card/focus/focus-error`) and replace existing inline uses inside `index.css` itself.
- [x] T04 Add `--accent-purple`, `--accent-blue`, `--bg-modal-overlay`, `--transition-fast`, `--transition-default`.
- [x] T05 Group `:root` block by category with section comments per R4; verify `make check` (frontend) still green.

### P2 - Module CSS sweep

One commit per logical batch (~5 files) for reviewable diffs. Order: shared `components/` first (highest reuse), then `pages/` per resource.

- [x] T06 Sweep `components/` batch 1: `Breadcrumb`, `BlinkingCursor`, `ConfirmDialog`, `EditableSection`, `EntryForm`.
- [x] T07 Sweep `components/` batch 2: `InlineCreateForm`, `LinkPickerModal`, `LinksPanel`, `LoadingSpinner`, `MarkdownContent`.
- [x] T08 Sweep `components/` batch 3: `Navigation`, `NotFound`, `SectionCard`, `StatusMessage`, `TagInput`.
- [x] T09 Sweep `components/` batch 4 (remaining): `CommunicationsPanel`, `LandingPage/LandingPage`.
- [x] T10 Sweep `pages/home/HomeView`.
- [x] T11 Sweep `pages/resumes/*` module CSS.
- [x] T12 Sweep `pages/applications/*` module CSS.
- [x] T13 Sweep `pages/accomplishments/*` module CSS.
- [x] T14 Sweep `pages/notes/*` module CSS.
- [x] T15 Sweep `pages/contacts/*` module CSS.
- [x] T16 Drop the `--radius` alias from T02 once no module references it; grep to confirm zero callers.

### P3 - Verification + docs

- [x] T17 Grep `frontend/src` for residual `#[0-9a-f]{3,8}`, `rgba(`, `box-shadow:` literals, and `[0-9.]+rem` on margin/padding/gap properties — resolve holdouts.
- [x] T18 Add 5-line "tokens-only" note to `frontend/AGENTS.md` (or `index.css` header comment) per R4.
- [x] T19 Take before/after screenshots of one list page (e.g., `/resumes`) and one detail page (e.g., a contact detail) at 1280px and 375px; attach to PR.
- [x] T20 `make check` (root) green; manual smoke per R3 across all six top-level pages.

### Implementation Notes

* **Sequence**: P1 strict-before P2 (sweep needs tokens to exist). Within P2, batches are independent — parallelize across an agent fleet if desired, but serial review is cleaner.
* **Snap deltas are intentional**: do not chase pixel-perfect parity by inventing extra `--space-*` steps. The point of this plan is to *normalize*; one-off literals defeat that.
* **Stray colors**: if the sweep finds a color that has no good semantic token, prefer adding a new token over keeping the literal. Each new token is cheap; each literal is a future audit miss.
* **No new deps**: pure CSS refactor, zero `package.json` change.
* **Coordinates with R012 (Storybook)**: a token gallery story is the natural next step, but not blocking. Once tokens land, Storybook can pull `:root` directly.
* **Coordinates with future dark/light**: keep token *names* semantic (`--bg-primary`, not `--gray-900`). Already the convention — preserve it.
