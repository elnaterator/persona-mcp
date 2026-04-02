# Tasks: UX Overhaul — Terminal-Inspired Dark Theme & Interface Improvements

**Input**: Design documents from `/specs/014-ux-overhaul/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, quickstart.md ✓

**Organization**: Tasks grouped by user story for independent implementation and testing.
**Tests**: Included for new components and changed behaviors only (not for CSS-only changes).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no cross-task dependencies)
- **[Story]**: Which user story this task belongs to (US1–US6)

---

## Phase 1: Setup

**Purpose**: Add `lucide-react` icon library dependency before any component work begins.

- [x] T001 Add `lucide-react` to dependencies in `frontend/package.json` and run `npm install` in `frontend/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the design token system (CSS custom properties) that every CSS module rewrite will reference. MUST complete before any dark theme or component styling work.

⚠️ **CRITICAL**: All Phase 3+ CSS work depends on these variables being defined first.

- [x] T002 Define all CSS custom properties (design tokens) on `:root` in `frontend/src/index.css`: background variables (`--bg-primary: #0a0a0a`, `--bg-secondary: #141414`, `--bg-surface: #1a1a1a`, `--bg-hover: #242424`), text variables (`--text-primary: #e0e0e0`, `--text-secondary: #888888`, `--text-muted: #555555`), accent variables (`--accent-green: #00ff41`, `--accent-green-dim: #00cc33`, `--accent-green-bg: rgba(0,255,65,0.08)`), border variables (`--border-primary: #2a2a2a`, `--border-hover: #3a3a3a`), status variables (`--status-success: #00ff41`, `--status-error: #ff4444`, `--status-warning: #ffaa00`), typography variable (`--font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', ui-monospace, monospace`), and `--radius: 0px` (sharp corners everywhere)

**Checkpoint**: Design tokens defined — all CSS module rewrites can now begin in parallel.

---

## Phase 3: User Story 1 — Terminal-Inspired Dark Theme Applied Site-Wide (Priority: P1) 🎯 MVP

**Goal**: Every page and component renders with the dark terminal aesthetic — dark backgrounds, monospace font, sharp corners, green accent, no white areas.

**Independent Test**: Open the app in a browser. Verify all backgrounds are dark, all text is in a monospace font, no rounded borders appear on buttons/inputs/cards, and a green blinking cursor accent is visible in the header.

### Implementation

- [x] T003 [US1] Update base styles in `frontend/src/index.css`: set `body { font-family: var(--font-mono); background-color: var(--bg-primary); color: var(--text-primary); }`, update `.app-header { background-color: var(--bg-secondary); border-bottom: 1px solid var(--border-primary); box-shadow: none; }`, update `main { background-color: var(--bg-surface); border-radius: 0; box-shadow: none; }`, update all `button`, `input`, `textarea` to use `border-radius: 0`, dark backgrounds, and `var(--font-mono)`; update link and heading colors to use CSS variables; update all media query breakpoint styles to match dark theme
- [x] T004 [P] [US1] Rewrite `frontend/src/components/Navigation.module.css`: `.nav` dark background; `.navItem` uses `var(--text-secondary)`, `var(--font-mono)`, `border-radius: 0`; `.navItem:hover` uses `var(--bg-hover)`, `var(--text-primary)`; `.navItem.active` uses `var(--accent-green-bg)`, `var(--accent-green)`, bottom border `1px solid var(--accent-green)` instead of rounded highlight
- [x] T005 [P] [US1] Rewrite `frontend/src/components/ConnectView/ConnectView.module.css`: all backgrounds to `var(--bg-surface)`/`var(--bg-primary)`, text to `var(--text-primary)`/`var(--text-secondary)`, borders to `var(--border-primary)`, `border-radius: 0` everywhere, warning banner recolored using `--status-warning`, buttons dark-styled with green accent on active/focus
- [x] T006 [P] [US1] Rewrite `frontend/src/components/ResumeListView.module.css`: dark backgrounds, `var(--text-primary)` text, `var(--border-primary)` borders, `border-radius: 0` on all elements, status badges recolored for dark theme (use muted green/red/amber on dark background), action buttons use dark styling with `var(--accent-green)` for primary actions
- [x] T007 [P] [US1] Rewrite `frontend/src/components/ResumeDetailView.module.css`: dark backgrounds, sharp corners, `var(--text-primary)` for content, `var(--text-secondary)` for labels/dates, `var(--border-primary)` for section dividers
- [x] T008 [P] [US1] Rewrite `frontend/src/components/EditableSection.module.css`: `.container` background `var(--bg-surface)`, `.header` with `var(--border-primary)` bottom border, `.title` uses `var(--text-primary)`, `.button` uses dark styling with `var(--accent-green)` for primary button, `border-radius: 0`
- [x] T009 [P] [US1] Rewrite `frontend/src/components/ContactSection.module.css`: all form fields and labels use dark theme variables, `border-radius: 0`, focus states use `var(--accent-green)` border
- [x] T010 [P] [US1] Rewrite `frontend/src/components/SummarySection.module.css`: dark theme variables, `border-radius: 0`, textarea focus with `var(--accent-green)` border
- [x] T011 [P] [US1] Rewrite `frontend/src/components/ExperienceSection.module.css`: dark theme variables, `border-radius: 0`, entry list items with `var(--border-primary)` dividers
- [x] T012 [P] [US1] Rewrite `frontend/src/components/EducationSection.module.css`: dark theme variables, `border-radius: 0`, same pattern as ExperienceSection
- [x] T013 [P] [US1] Rewrite `frontend/src/components/SkillsSection.module.css`: dark theme variables, `border-radius: 0`, skill category headers use `var(--text-secondary)`
- [x] T014 [P] [US1] Rewrite `frontend/src/components/ConfirmDialog.module.css`: overlay background `rgba(0,0,0,0.7)`, dialog background `var(--bg-surface)`, `border: 1px solid var(--border-primary)`, `border-radius: 0`, buttons dark-styled, destructive button uses `var(--status-error)`
- [x] T015 [P] [US1] Rewrite `frontend/src/components/StatusMessage.module.css`: dark theme success (green tint on dark bg), error (red tint on dark bg), `border-radius: 0`, monospace text
- [x] T016 [P] [US1] Rewrite `frontend/src/components/EntryForm.module.css`: all inputs/labels use dark theme, `border-radius: 0`, `var(--accent-green)` focus states
- [x] T017 [P] [US1] Rewrite `frontend/src/components/LoadingSpinner.module.css`: spinner uses `var(--accent-green)` color on dark background
- [x] T018 [P] [US1] Rewrite `frontend/src/components/Breadcrumb.module.css`: `var(--text-muted)` for crumbs, `var(--text-secondary)` for separators, `var(--accent-green)` for active/current crumb
- [x] T019 [P] [US1] Rewrite `frontend/src/components/ApplicationListView.module.css`: dark theme variables, `border-radius: 0`, status badges recolored for dark bg, search/filter inputs use dark styling
- [x] T020 [P] [US1] Rewrite `frontend/src/components/ApplicationDetailView.module.css`: dark theme variables, `border-radius: 0`, section headers use `var(--text-secondary)` with `var(--border-primary)` dividers
- [x] T021 [P] [US1] Rewrite `frontend/src/components/ContactsPanel.module.css` (if exists, else skip): dark theme variables, `border-radius: 0`
- [x] T022 [P] [US1] Rewrite `frontend/src/components/CommunicationsPanel.module.css` (if exists, else skip): dark theme variables, `border-radius: 0`
- [x] T023 [P] [US1] Rewrite `frontend/src/components/AccomplishmentListView.module.css`: dark theme variables, `border-radius: 0`
- [x] T024 [P] [US1] Rewrite `frontend/src/components/AccomplishmentDetailView.module.css`: dark theme variables, `border-radius: 0`, STAR fields use `var(--text-secondary)` labels
- [x] T025 [P] [US1] Rewrite `frontend/src/components/NoteListView.module.css`: dark theme variables, `border-radius: 0`, tags use muted green chips
- [x] T026 [P] [US1] Rewrite `frontend/src/components/NoteDetailView.module.css`: dark theme variables, `border-radius: 0`
- [x] T027 [P] [US1] Rewrite `frontend/src/components/UserMenu/index.module.css` (or wherever UserMenu CSS lives): dark theme variables, `border-radius: 0`, dropdown uses `var(--bg-surface)` with `var(--border-primary)` border
- [x] T028 [P] [US1] Rewrite `frontend/src/components/LandingPage/index.module.css` (or wherever LandingPage CSS lives): dark full-page background, centered sign-in card in `var(--bg-surface)`, `border-radius: 0`
- [x] T029 [US1] Create `frontend/src/components/BlinkingCursor.tsx`: functional component that renders a `<span>` with CSS class for green blinking cursor; and create `frontend/src/components/BlinkingCursor.module.css` with `@keyframes blink { 0%, 100% { opacity: 1 } 50% { opacity: 0 } }` using `animation: blink 1s steps(1) infinite`, background `var(--accent-green)`, dimensions `2px wide × 1.2em tall`, display `inline-block`
- [x] T030 [US1] Add `<BlinkingCursor />` next to the app title `<h1>` in `frontend/src/App.tsx` (inside `.app-header-inner`, after the h1 text)

**Checkpoint**: All pages render with dark terminal aesthetic. Verify: dark backgrounds everywhere, monospace font, sharp corners, green blinking cursor in header.

---

## Phase 4: User Story 2 — Connect Tab as the Default Landing Page (Priority: P2)

**Goal**: Logging in routes to `/connect` instead of `/resumes`. The Connect tab is visually distinct in the nav.

**Independent Test**: Log in. Verify the Connect tab is active and its content is displayed. Verify URL is `/connect`. Navigate to `/` — confirm redirect to `/connect`.

### Implementation

- [x] T031 [US2] Update default redirect in `frontend/src/router.tsx`: change `<Route path="/" element={<Navigate to="/resumes" replace />} />` to `<Route path="/" element={<Navigate to="/connect" replace />} />` and update the catch-all `<Route path="*" element={<Navigate to="/resumes" replace />} />` to redirect to `/connect`

**Checkpoint**: After login, user lands on Connect tab. Navigating to `/` or any unknown route redirects to `/connect`.

---

## Phase 5: User Story 3 — Connect Page Decluttered and Visually Appealing (Priority: P3)

**Goal**: Connect tab feels like a polished landing page — clear primary action, breathing room, vertical progressive flow, generated output as focal point.

**Independent Test**: Log in, land on Connect tab. The primary purpose (connect an AI assistant) is clear at a glance without scrolling. The API key area is the visual focal point. Config snippets only expand after a key is pasted.

### Implementation

- [x] T032 [US3] Restructure `frontend/src/components/ConnectView/index.tsx`: replace two-column grid layout with a single vertical column; move heading and one-sentence description to a hero section at top with `<BlinkingCursor />`; place `<APIKeys />` as the primary focal element with a clear "Step 1" label; move the paste-key input below as "Step 2"; render assistant tabs and config snippets below as "Step 3" — dim or visually de-emphasize the snippet section when no key is pasted (add `apiKey.trim() === ''` conditional styling); remove or collapse the warning banner into a smaller inline hint next to the paste input
- [x] T033 [US3] Rewrite `frontend/src/components/ConnectView/ConnectView.module.css` for the new single-column layout: `.container` with generous padding and `max-width: 640px` centered; `.hero` section with large heading, cursor, and subtext; `.step` numbered sections with `var(--border-primary)` left border accent and `var(--text-muted)` step number; `.snippetsSection` with `opacity: 0.4` when no key pasted (add `.snippetsSectionActive` class toggled via JS); assistant tabs use `var(--accent-green)` active indicator; remove all `border-radius`, use sharp lines

**Checkpoint**: Connect page renders as a focused, uncluttered vertical flow. Config snippets are de-emphasized until a key is pasted.

---

## Phase 6: User Story 4 — Improved Navigation Bar with Icons (Priority: P4)

**Goal**: Each nav tab has a `lucide-react` icon, the active tab is clearly highlighted, hover states are visible, and the Connect tab is visually accented as the primary destination.

**Independent Test**: View the navigation bar. Each of the 5 tabs shows a relevant icon alongside its label. The active tab is immediately distinguishable. Hovering an inactive tab shows a clear state change. Connect tab has additional visual weight.

### Implementation

- [x] T056 [P] [US4] Update `frontend/src/components/Navigation.tsx`: import icons from `lucide-react` — `Terminal` (Connect), `FileText` (Resumes), `Briefcase` (Applications), `Trophy` (Accomplishments), `StickyNote` (Notes); wrap each `NavLink` content to render `<Icon size={16} /> Label` with the appropriate icon; add a `connectItem` CSS class to the Connect `NavLink` for special treatment
- [x] T057 [P] [US4] Update `frontend/src/components/Navigation.module.css`: add `.navItem` flex layout (`display: flex; align-items: center; gap: 0.375rem`) to accommodate icons; add `.connectItem` class: `var(--accent-green)` text color, `border-bottom: 2px solid var(--accent-green)` always visible (not just active), slightly brighter on hover; update `.navItem.active` to use `var(--accent-green)` color and a bottom border accent; update `.navItem:hover` for dark hover background

**Checkpoint**: Navigation bar shows icons on all tabs. Connect tab is visually prominent. Active and hover states are clearly distinguishable.

---

## Phase 7: User Story 5 — Resume Section Looks Like a Real Resume (Priority: P5)

**Goal**: Resume tab renders as a document-like layout at rest. Edit controls only appear on hover (desktop) or first tap (mobile). Empty resume shows labeled section placeholders with "Click to add" prompts.

**Independent Test**: Open Resume tab with populated data. Verify the layout resembles a resume document — no visible edit buttons at rest. Hover over a section — verify an edit icon appears. Click to edit, save, verify the read view restores. Open Resume tab with empty resume — verify structured section placeholders are visible.

### Implementation

- [x] T034 [US5] Refactor `frontend/src/components/EditableSection.tsx`: add `hovering` state (boolean); add `onMouseEnter`/`onMouseLeave` handlers on the container div to set `hovering`; add `onTouchStart` handler that sets `hovering: true` (cleared after 3s timeout or on blur); show the Edit button/icon only when `hovering === true` OR `editState === 'editing'` OR `editState === 'saving'`; render the edit affordance as a small pencil icon (`<Pencil size={14} />` from lucide-react) positioned absolutely at top-right of the section container, fading in/out via CSS transition; update `EditableSectionProps` to accept optional `placeholderContent?: ReactNode` for empty state rendering
- [x] T035 [US5] Update `frontend/src/components/EditableSection.module.css`: `.container { position: relative }` to anchor the absolute edit icon; add `.editIcon { position: absolute; top: 0.5rem; right: 0.5rem; opacity: 0; transition: opacity 0.15s; color: var(--accent-green); cursor: pointer; }` and `.container:hover .editIcon, .editIcon.visible { opacity: 1; }`; update `.header` to remove the persistent button row styling (header only needed when in editing/saving state)
- [x] T036 [P] [US5] Redesign `frontend/src/components/ContactSection.tsx` read view: when `isEditing === false`, render name as large heading (`var(--text-primary)`), then contact details (email · phone · location · linkedin · website · github) as a single inline row separated by `·` using `var(--text-secondary)`; this is the resume document header
- [x] T037 [P] [US5] Update `frontend/src/components/ContactSection.module.css`: `.readView` with large name heading, inline contact row, no borders or boxes
- [x] T038 [P] [US5] Redesign `frontend/src/components/SummarySection.tsx` read view: render summary text as a plain paragraph with `var(--text-primary)`, section heading "SUMMARY" in uppercase `var(--text-secondary)` small text with a `var(--border-primary)` underline
- [x] T039 [P] [US5] Update `frontend/src/components/SummarySection.module.css`: section heading with uppercase label + border bottom, body text readable, no card wrappers
- [x] T040 [P] [US5] Redesign `frontend/src/components/ExperienceSection.tsx` read view: render each entry as title (bold) + company (regular) + dates/location (muted, right-aligned or inline), followed by bullet points for highlights in a `<ul>`; section heading "EXPERIENCE" uppercase with border; show "Click to add" placeholder entry when `experience` array is empty
- [x] T041 [P] [US5] Update `frontend/src/components/ExperienceSection.module.css`: entry layout with title bold, company + date inline row, bullet list flush left, `var(--border-primary)` separator between entries
- [x] T042 [P] [US5] Redesign `frontend/src/components/EducationSection.tsx` read view: same pattern as experience — degree + field (bold), institution (regular), dates (muted); section heading "EDUCATION" uppercase with border; "Click to add" placeholder when empty
- [x] T043 [P] [US5] Update `frontend/src/components/EducationSection.module.css`: same patterns as ExperienceSection.module.css
- [x] T044 [P] [US5] Redesign `frontend/src/components/SkillsSection.tsx` read view: render skills as inline comma-separated groups by category (e.g., "Languages: Python, Go, TypeScript · Frameworks: FastAPI, React"); section heading "SKILLS" uppercase with border; "Click to add" placeholder when empty
- [x] T045 [P] [US5] Update `frontend/src/components/SkillsSection.module.css`: inline skill groups with `var(--text-secondary)` category labels
- [x] T046 [US5] Update `frontend/src/components/ResumeDetailView.tsx`: render sections in document order (Contact → Summary → Experience → Education → Skills); remove card-style wrappers; add resume document container with max-width ~800px centered; ensure section ordering matches a traditional resume; pass `placeholderContent` to each `EditableSection` for empty state
- [x] T047 [US5] Update `frontend/src/components/ResumeDetailView.module.css`: `.document` container with `max-width: 800px`, `margin: 0 auto`, document-style padding; `var(--bg-surface)` background with 1px `var(--border-primary)` border; sections separated by `1px solid var(--border-primary)` horizontal rules, not cards

**Checkpoint**: Resume tab renders as a document. No edit UI at rest. Hover reveals pencil icon. Edit, save, cancel all work. Empty sections show "Click to add" placeholders.

---

## Phase 8: User Story 6 — Add New Resume Version Without an Alert Dialog (Priority: P6)

**Goal**: Clicking "Add Version" expands an inline form within the resume list — no native browser `window.prompt()` dialog. Validates version name. Dismissible.

**Independent Test**: Click "Add Version". Verify no browser dialog appears. Verify a styled input form expands inline. Enter a name, confirm — new version appears in list. Click cancel or press Escape — form collapses, no version created. Submit empty name — inline error appears, no submission.

### Implementation

- [x] T048 [US6] Create `frontend/src/components/InlineCreateForm.tsx`: props `{ onConfirm: (label: string) => Promise<void>; onCancel: () => void; placeholder?: string; confirmLabel?: string }`; local state: `value` (string), `error` (string|null), `submitting` (boolean); auto-focus input on mount (`useRef` + `useEffect`); Escape key listener that calls `onCancel`; validate: if `value.trim() === ''` set error "Name cannot be empty", abort submission; call `onConfirm(value.trim())` on submit, set `submitting: true` during await, catch errors and display inline; render as a form with a labeled text input, a confirm button (disabled while submitting), a cancel button, and an inline error message area
- [x] T049 [US6] Create `frontend/src/components/InlineCreateForm.module.css`: `.form` with `var(--bg-hover)` background, `1px solid var(--accent-green)` left border accent (terminal prompt feel), `border-radius: 0`, padding; `.input` dark-styled with `var(--accent-green)` focus border; `.confirmBtn` with `var(--accent-green)` color; `.cancelBtn` muted; `.error` with `var(--status-error)` color, small font size; smooth expand animation optional
- [x] T050 [US6] Update `frontend/src/components/ResumeListView.tsx`: add `creating` state (boolean); replace `handleCreate` function (which calls `window.prompt`) with `setCreating(true)`; render `<InlineCreateForm>` conditionally when `creating === true` (insert it above the resume list or below the "Add Version" button); `onConfirm` calls `createResume(label)` then `load()` then `setCreating(false)`; `onCancel` calls `setCreating(false)`

**Checkpoint**: Resume list has no `window.prompt` call. Inline form opens, validates, creates version, and dismisses cleanly.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Component tests for new behaviors, final quality pass.

- [x] T051 [P] Write Vitest component tests for `InlineCreateForm` in `frontend/src/__tests__/InlineCreateForm.test.tsx`: test renders correctly, auto-focuses input, shows error on empty submit, calls onConfirm with trimmed value, calls onCancel on Escape key, disables button while submitting
- [x] T052 [P] Write Vitest component tests for updated `EditableSection` hover behavior in `frontend/src/__tests__/EditableSection.test.tsx`: test edit icon is not visible at rest, appears on mouse enter, activates editing on click, discards on cancel, edit icon visible during editing state
- [x] T053 [P] Write Vitest component tests for `Navigation` icons in `frontend/src/__tests__/Navigation.test.tsx`: test all 5 nav items render with icons, Connect NavLink has `connectItem` class, active state reflects current route
- [x] T054 Run `make check` from `frontend/` directory (lint + typecheck + test) and fix any failures
- [x] T055 Update `README.md` at repo root: document the new dark theme, Connect tab as landing page, and that the application requires no theme configuration (dark is the only theme)

---

## Phase 10: Manual UI Tweaks — Look & Feel Polish

**Purpose**: Post-implementation visual fine-tuning based on real usage. All tasks are manual — no automated tests required. Apply changes incrementally and eyeball results in the browser.

- [x] T058 Use a darker more forest green, not so bright, remove underlines, boxes, etc., keep it more simple and minimalist for buttons, header links
- [x] T059 Remove the underlines from the connect and selected header nav links, use a different color background when selected, remove the line separator between the header and body, remove the box outline from the active navlink
- [x] T060 Remove the outlines and boxes from all sections and buttons, have no borders anywhere, use a slightly diff background color instead to mark a button or section
- [x] T061 The body should look minimalist and flat and be 1 background color from edge to edge, no borders or lines, use a dark charcoal background

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all CSS module work
- **Phase 3 (US1 Dark Theme)**: Depends on Phase 2; T003 must complete before other T004–T028 (body styles set in T003 affect all)
- **Phase 4 (US2 Default Route)**: Depends only on Phase 1 — can run in parallel with Phase 3
- **Phase 5 (US3 Connect Declutter)**: Depends on Phase 3 (dark theme CSS) being applied to ConnectView; also uses BlinkingCursor from Phase 3 (T029)
- **Phase 6 (US4 Nav Icons)**: Depends on Phase 3 (dark theme nav CSS), Phase 1 (lucide-react installed). Tasks: T056–T057
- **Phase 7 (US5 Resume Layout)**: T034 (EditableSection) must complete before T036–T045 (section components); T046–T047 (ResumeDetailView) depend on T034–T045
- **Phase 8 (US6 Inline Form)**: T048–T049 (InlineCreateForm) before T050 (ResumeListView); independent of Phases 5–7
- **Phase 9 (Polish)**: T051–T053 tests can run after their respective component phases complete; T054 after all implementation

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational phase — no story dependencies
- **US2 (P2)**: Independent of US1 — can run in parallel with Phase 3
- **US3 (P3)**: Depends on US1 dark theme applied to ConnectView + BlinkingCursor (T029–T030)
- **US4 (P4)**: Depends on US1 dark theme applied to Navigation + lucide-react installed (T001)
- **US5 (P5)**: Depends on US1 dark theme applied to resume components
- **US6 (P6)**: Depends on US1 dark theme applied to ResumeListView; independent of US3–US5

### Within Phase 3 (US1 Dark Theme)

- T003 (body/base styles) first
- T004–T028 all [P] — can run in parallel (all modify different files)
- T029 (BlinkingCursor component) and T030 (place in App.tsx) in sequence

### Within Phase 7 (US5 Resume Layout)

- T034 (EditableSection.tsx) → T035 (EditableSection.module.css) in sequence
- T036–T045 (section components) all [P] with each other, but depend on T034
- T046–T047 (ResumeDetailView) depend on T036–T045 being complete

---

## Parallel Opportunities

```bash
# Phase 3: Launch all CSS module rewrites together (after T002 and T003):
T004 Navigation.module.css          ← different file
T005 ConnectView.module.css         ← different file
T006 ResumeListView.module.css      ← different file
T007 ResumeDetailView.module.css    ← different file
T008 EditableSection.module.css     ← different file
T009–T013 Section CSS modules       ← different files
T014–T018 Utility component CSS     ← different files
T019–T028 App + remaining CSS       ← different files

# Phase 7: Launch section component rewrites together (after T034):
T036 ContactSection.tsx + T037 ContactSection.module.css
T038 SummarySection.tsx + T039 SummarySection.module.css
T040 ExperienceSection.tsx + T041 ExperienceSection.module.css
T042 EducationSection.tsx + T043 EducationSection.module.css
T044 SkillsSection.tsx + T045 SkillsSection.module.css

# Phase 9: All test tasks in parallel:
T051 InlineCreateForm.test.tsx
T052 EditableSection.test.tsx
T053 Navigation.test.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup (`npm install lucide-react`)
2. Complete Phase 2: Foundational (CSS custom properties)
3. Complete Phase 3: US1 Dark Theme (site-wide visual overhaul)
4. Complete Phase 4: US2 Default Route (single line change)
5. **STOP and VALIDATE**: Dark terminal aesthetic visible everywhere + Connect is landing page
6. Demo or deploy if ready

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. Phase 3 → Dark theme (US1) — biggest visual impact, MVP
3. Phase 4 → Connect as landing (US2) — one line change
4. Phase 5 → Connect decluttered (US3) — landing page polished
5. Phase 6 → Nav icons (US4) — navigational clarity
6. Phase 7 → Resume layout + hover edit (US5) — resume quality
7. Phase 8 → Inline version creation (US6) — UX anti-pattern removed
8. Phase 9 → Tests + README

---

## Notes

- [P] tasks modify different files — safe to run concurrently
- CSS module rewrites (Phase 3) are the most numerous but entirely parallelizable
- T034 (EditableSection refactor) is the highest-risk task — test it standalone before proceeding to T036–T045
- `window.prompt` removal (T050) is a direct find-and-replace in `ResumeListView.tsx` — low risk
- The BlinkingCursor component (T029) is self-contained and can be validated before App.tsx integration (T030)
- Run `make check` in `frontend/` after each phase checkpoint to catch type errors early
- Commit after each phase checkpoint or logical group of tasks
