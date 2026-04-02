# Implementation Plan: UX Overhaul — Terminal-Inspired Dark Theme & Interface Improvements

**Branch**: `014-ux-overhaul` | **Date**: 2026-03-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-ux-overhaul/spec.md`

## Summary

Redesign the Persona frontend with a terminal-inspired dark theme (monospace typography, sharp corners, green cursor accent), restructure navigation with icons and Connect as the default landing tab, declutter the Connect page, replace resume editing with a hover-to-edit resume-like layout, and replace the native `window.prompt()` for resume version creation with a styled inline form. This is a **frontend-only** feature — no backend changes, no new API endpoints, no data model changes.

## Technical Context

**Language/Version**: TypeScript 5.x / React 18
**Primary Dependencies**: React Router v7, Vite 6, CSS Modules, `@clerk/clerk-react` v5, `lucide-react` (new — icon library)
**Storage**: N/A — no storage changes
**Testing**: Vitest 2 with React Testing Library
**Target Platform**: Web browsers (desktop + mobile)
**Project Type**: Web application (frontend only for this feature)
**Performance Goals**: Standard web app — all pages render within 1s, no layout shifts during theme application
**Constraints**: No additional CSS framework (keep CSS Modules); single new dependency (`lucide-react`) for icons
**Scale/Scope**: ~20 component files modified, ~5 new component files, ~25 CSS module files rewritten

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | N/A | No MCP changes — frontend-only |
| II. Single-Package Distribution | N/A | No packaging changes |
| III. Test-Driven Development | PASS | Component tests required for new UI behaviors (inline edit, version creation form, nav icons). Vitest + RTL is the established frontend test runner. |
| IV. Minimal Dependencies | PASS | One new dependency: `lucide-react` — tree-shakable icon library, MIT license, zero transitive deps, only imports needed icons. Justified: hand-coding SVG icons for 5+ nav items + UI controls is prohibitive and error-prone. |
| V. Explicit Error Handling | N/A | No new MCP tool handlers |
| Makefile targets | PASS | Existing `make check`, `make lint`, `make test` cover frontend |
| Branching | PASS | Branch `014-ux-overhaul` follows accepted `<NNN>-<name>` pattern |
| README updates | PASS | Task included to update README with UX changes |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/014-ux-overhaul/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (minimal — no data changes)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (empty — no API changes)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   ├── Navigation.tsx              # Modified: add icons, Connect highlighting, dark theme
│   │   ├── Navigation.module.css       # Rewritten: dark theme, icons, sharp corners
│   │   ├── ConnectView/
│   │   │   ├── index.tsx               # Modified: restructured layout, decluttered
│   │   │   └── ConnectView.module.css  # Rewritten: dark theme, spacious layout
│   │   ├── ResumeListView.tsx          # Modified: inline form replaces window.prompt
│   │   ├── ResumeListView.module.css   # Rewritten: dark theme
│   │   ├── ResumeDetailView.tsx        # Modified: resume-like layout with hover-to-edit
│   │   ├── ResumeDetailView.module.css # Rewritten: resume layout + dark theme
│   │   ├── EditableSection.tsx         # Modified: hover-triggered edit mode, hide controls at rest
│   │   ├── EditableSection.module.css  # Rewritten: hover reveal, dark theme
│   │   ├── ContactSection.tsx          # Modified: resume-like read view, inline edit on hover
│   │   ├── ContactSection.module.css   # Rewritten
│   │   ├── SummarySection.tsx          # Modified: resume-like read view
│   │   ├── SummarySection.module.css   # Rewritten
│   │   ├── ExperienceSection.tsx       # Modified: resume-like read view
│   │   ├── ExperienceSection.module.css# Rewritten
│   │   ├── EducationSection.tsx        # Modified: resume-like read view
│   │   ├── EducationSection.module.css # Rewritten
│   │   ├── SkillsSection.tsx           # Modified: resume-like read view
│   │   ├── SkillsSection.module.css    # Rewritten
│   │   ├── ConfirmDialog.tsx           # Modified: dark theme styling
│   │   ├── ConfirmDialog.module.css    # Rewritten
│   │   ├── StatusMessage.tsx           # Modified: dark theme styling
│   │   ├── StatusMessage.module.css    # Rewritten
│   │   ├── EntryForm.tsx               # Modified: dark theme form styling
│   │   ├── EntryForm.module.css        # Rewritten
│   │   ├── InlineCreateForm.tsx        # NEW: reusable inline form (replaces window.prompt)
│   │   ├── InlineCreateForm.module.css # NEW
│   │   ├── BlinkingCursor.tsx          # NEW: green blinking cursor accent component
│   │   ├── BlinkingCursor.module.css   # NEW
│   │   ├── LoadingSpinner.module.css   # Rewritten: dark theme
│   │   ├── Breadcrumb.module.css       # Rewritten: dark theme
│   │   ├── ApplicationListView.module.css    # Rewritten: dark theme
│   │   ├── ApplicationDetailView.module.css  # Rewritten: dark theme
│   │   ├── AccomplishmentListView.module.css # Rewritten: dark theme
│   │   ├── AccomplishmentDetailView.module.css # Rewritten: dark theme
│   │   ├── NoteListView.module.css           # Rewritten: dark theme
│   │   ├── NoteDetailView.module.css         # Rewritten: dark theme
│   │   ├── UserMenu/index.module.css         # Rewritten: dark theme
│   │   └── LandingPage/index.module.css      # Rewritten: dark theme
│   ├── index.css            # Rewritten: dark theme base, monospace font, sharp corners, CSS custom properties
│   ├── router.tsx           # Modified: default route / → /connect
│   └── __tests__/           # Modified + new tests for inline edit, nav icons, version form
└── package.json             # Modified: add lucide-react dependency
```

**Structure Decision**: Existing web application structure. All changes within `frontend/` directory. No backend modifications.

## Complexity Tracking

No constitution violations — this section is empty.

## Design Decisions

### D1: CSS Custom Properties for Theme

Define all colors, spacing, and typography as CSS custom properties in `index.css` on `:root`. All component CSS modules reference these variables instead of hardcoded values. This enables:
- Single source of truth for the dark theme palette
- Easy future extension to light mode if desired
- Consistent application across all components

```css
:root {
  /* Backgrounds */
  --bg-primary: #0a0a0a;
  --bg-secondary: #141414;
  --bg-surface: #1a1a1a;
  --bg-hover: #242424;
  --bg-active: #1a2e1a;

  /* Text */
  --text-primary: #e0e0e0;
  --text-secondary: #888888;
  --text-muted: #555555;

  /* Accent */
  --accent-green: #00ff41;
  --accent-green-dim: #00cc33;
  --accent-green-bg: rgba(0, 255, 65, 0.08);

  /* Borders */
  --border-primary: #2a2a2a;
  --border-hover: #3a3a3a;

  /* Status */
  --status-success: #00ff41;
  --status-error: #ff4444;
  --status-warning: #ffaa00;

  /* Typography */
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', ui-monospace, monospace;

  /* Spacing (consistent scale) */
  --radius: 0px; /* sharp corners everywhere */
}
```

### D2: Icon Library — lucide-react

**Decision**: Use `lucide-react` for navigation and UI icons.

**Rationale**:
- Tree-shakable — only imported icons are bundled
- MIT license, zero transitive dependencies
- Consistent 24x24 SVG design system
- Already widely used in React ecosystem
- Alternatives considered: heroicons (heavier), hand-coded SVGs (maintenance burden), react-icons (massive package)

**Icons planned**:
- Connect: `Terminal` or `Plug`
- Resumes: `FileText`
- Applications: `Briefcase`
- Accomplishments: `Trophy`
- Notes: `StickyNote`
- Edit actions: `Pencil`, `Check`, `X`
- Add: `Plus`
- Copy: `Copy`, `ClipboardCheck`

### D3: EditableSection Refactor — Hover-to-Edit

The current `EditableSection` shows an explicit "Edit" button at all times. The new pattern:

1. **Read state** (default): No edit UI visible. Content renders in resume-like format.
2. **Hover state**: A subtle edit icon (pencil) fades in at the top-right corner of the section. On touch devices, the first tap triggers this state.
3. **Edit state**: Clicking the edit icon transitions to inline editing. Save/Cancel controls appear. Escape key cancels.
4. **Saving state**: "Saving..." indicator replaces controls (existing behavior).
5. **Navigation during edit**: Unsaved changes discarded silently (per clarification).

The `EditableSection` component gains:
- `onMouseEnter`/`onMouseLeave` handlers for hover detection
- `onTouchStart` handler for mobile tap-to-reveal
- A `hovering` state that controls edit icon visibility
- CSS transitions for smooth fade in/out of the edit icon

### D4: Resume-Like Layout

The `ResumeDetailView` renders as a document-style page:
- Name/contact info prominent at top (large name, contact details inline)
- Horizontal dividers between sections (1px solid lines)
- Section headings in uppercase or small-caps with left alignment
- Content in standard resume format (company | date range, bullet points for highlights)
- Max-width container centered, resembling a paper document on the dark background
- No card-style wrappers or shadows — just clean lines and whitespace

### D5: Connect Page Redesign

Current layout: Two-column grid (API keys | config snippets) — dense, all visible at once.

New layout:
1. **Hero section**: App title/logo with blinking cursor accent, one-line description
2. **Primary action**: "Generate API Key" as the prominent CTA — Clerk `<APIKeys />` component
3. **Secondary section**: Collapsible or stepped flow — paste key → select assistant → see config snippet
4. **Reduced visual weight**: Config snippets only expand after key is pasted, reducing initial clutter

### D6: InlineCreateForm Component

Replaces `window.prompt()` for resume version creation. A controlled form component that:
- Renders inline within the list (not a modal or overlay)
- Single text input with label "Version name"
- Submit (Enter or button) and Cancel (Escape or button) actions
- Inline validation: empty name shows error message, no submission
- Matches dark theme with green accent on focus
- Auto-focuses the input when opened
- Reusable for future inline creation flows

### D7: BlinkingCursor Component

A small decorative component that renders a terminal-style blinking cursor:
- Green rectangle (`var(--accent-green)`)
- CSS animation: `opacity` keyframes (1s cycle, step timing for authentic blink)
- Placed in the header area next to the app title
- Pure CSS animation — no JavaScript timers
