# Plan 001 - Update Landing Page With Latest Info

Date: 2026-05-01

Fix headline wrap on pre-signin landing page (`Your career data, organized.` breaking onto two lines) and expand feature card grid to cover all current + planned data types: Resumes, Applications, Accomplishments, Notes, Contacts.


## Requirements

### R1 - Headline renders single line

Hero headline `Your career data, organized.` must render on one line at standard desktop widths without truncation, ellipsis, or wrap.

* Renders single line at viewport widths ≥ 768px
* Wrap permitted at narrow viewports (< 640px) where mobile breakpoint already shrinks font
* No layout shift or overflow on resize between 640px–1280px
* Headline font weight, color, vertical rhythm preserved (no visual regression vs current other than wrap)
* `white-space: nowrap` not used at desktop widths if width can be solved structurally (prefer max-width + font-size tuning)


### R2 - Five feature cards on landing page

Features section lists all five data domains that Persona manages.

* Cards: Resumes, Applications, Accomplishments, Notes, Contacts (in that order)
* Each card has icon, title, one-sentence description matching tone of existing copy
* Grid layout adapts: 5 columns wide desktop (or 3+2 if 5-wide reads cramped), 2 cols tablet, 1 col mobile
* Card visual style identical to existing three (no per-card variation)
* Notes copy reflects current note feature (free-form notes with tags)
* Contacts copy describes intent (career networking) — flagged as forward-looking until contacts feature ships


## Design

**Files touched:**
- `frontend/src/components/LandingPage/index.tsx` — add 2 feature card entries
- `frontend/src/components/LandingPage/LandingPage.module.css` — widen `.hero` max-width OR reduce `.headline` font-size; adjust `.features` grid template

**Headline fix options (pick one in implementation):**
1. Widen `.hero` max-width from `600px` → ~`760px`. "Your career data, organized." at 2.5rem/700 needs ~720px render width.
2. Reduce `.headline` font-size from `2.5rem` → `2.25rem`. Less invasive but loses presence.
3. Combo: bump max-width to 720px + shave font 2.5→2.375rem. Safest.

Recommend option 3 — robust across font-loading + small viewport variance.

**Grid:**
- Desktop (>900px): `grid-template-columns: repeat(5, 1fr)` with `max-width` bumped from 800px → ~1100px to keep card density readable, OR keep 3-up row with 2-up row underneath via `repeat(3, 1fr)` and last 2 cards span. Prefer 5-up clean row; fallback 3+2 if cards become cramped (<160px each).
- Tablet (641–900px): `repeat(2, 1fr)` (current rule keeps; 5 items wrap to 3 rows = 2/2/1).
- Mobile (≤640px): `1fr` (current).

**Contacts copy (forward-looking):**
> "Track people you meet during your job search — recruiters, hiring managers, and connections."

Acceptable since landing page is marketing surface; users only see it pre-signin. If product owner wants strict "no advertise unshipped features" policy, gate on contacts feature ship date.

**No backend changes. No new deps. No tests required (presentational, no logic).**


## Tasks

### P1 - Headline single line

- [x] T01 Edit `LandingPage.module.css` — bump `.hero` max-width to 720px and reduce `.headline` font-size to 2.375rem
- [x] T02 Verify rendering at 1440px, 1024px, 768px, 640px, 375px in browser dev tools

### P2 - Add Notes + Contacts feature cards

- [x] T03 Edit `LandingPage/index.tsx` — append Notes card (icon `📝`, copy: "Capture free-form notes with tags — research, prep work, anything you want to recall later.")
- [x] T04 Edit `LandingPage/index.tsx` — append Contacts card (icon `🤝`, copy: "Track people you meet during your job search — recruiters, hiring managers, and connections.")
- [x] T05 Edit `LandingPage.module.css` `.features` — set desktop grid to `repeat(5, 1fr)`, bump `max-width` to 1100px; verify tablet (`repeat(2, 1fr)`) + mobile (`1fr`) still hold
- [x] T06 If 5-wide cards render <160px each at 1100px, fall back to `repeat(3, 1fr)` desktop (3+2 wrap)

### P3 - Verify

- [x] T07 Run `cd frontend && make check`
- [x] T08 Manual: load `/` signed-out at 1440/1024/768/640/375; confirm headline single line ≥ 768, all 5 cards present, grid responsive
- [x] T09 Confirm no regression on signed-in HomeView (separate component, should be untouched)


### Implementation Notes

- Sequence: P1 → P2 → P3. P1 + P2 independent in code but both touch same CSS file — do P1 first to avoid merge friction.
- Contacts feature itself is separate roadmap item ("Add contacts feature"). This plan only adds landing-page marketing card. Confirm with product owner before merging if forward-advertising policy unclear.
- No backend, no API, no test files. Pure presentational tweak.
- Icons use existing emoji pattern (`📄 💼 🏆`). Stay consistent — no `lucide-react` swap in this plan.
