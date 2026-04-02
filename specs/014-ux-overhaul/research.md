# Research: 014 UX Overhaul

## R1: Icon Library Selection

**Decision**: `lucide-react`
**Rationale**: Tree-shakable (only imported icons ship), MIT license, zero transitive dependencies, consistent 24px SVG system, excellent React integration with typed components. Bundle impact: ~2-3KB for 10 icons (gzipped).
**Alternatives considered**:
- `react-icons` — Aggregates many icon sets but ships 42MB unpacked; tree-shaking is possible but import paths are cumbersome
- `@heroicons/react` — Good quality but Tailwind-centric naming; slightly larger per-icon overhead
- Hand-coded SVGs — Zero dependency but high maintenance burden for 10+ icons, inconsistent sizing
- `@phosphor-icons/react` — Good alternative, slightly less popular, similar footprint

## R2: Monospace Font Strategy

**Decision**: Use system monospace font stack via CSS (no web font download required)
**Rationale**: `'JetBrains Mono', 'Fira Code', 'SF Mono', 'Cascadia Code', ui-monospace, monospace` provides high-quality monospace rendering on all platforms without a font download. Users with JetBrains Mono or Fira Code installed (common among developers — the target audience) get the premium experience; others fall back to their platform's default monospace. Adding a self-hosted web font (JetBrains Mono at ~100KB) could be a future enhancement but is unnecessary for the MVP given the target audience.
**Alternatives considered**:
- Self-hosted JetBrains Mono via `@font-face` — Guarantees consistent rendering but adds 100KB+ to initial load; premature for this feature
- Google Fonts CDN — External dependency, privacy concerns, GDPR implications
- Single fallback (`monospace`) — Too platform-dependent; rendering varies wildly

## R3: CSS Custom Properties vs CSS-in-JS vs Tailwind

**Decision**: CSS custom properties (CSS variables) in existing CSS Modules
**Rationale**: The project already uses CSS Modules. Introducing a new styling paradigm (Tailwind, styled-components, emotion) would be a large scope change touching every component. CSS custom properties provide theme-level abstraction within the existing CSS Module files. Variables defined on `:root` propagate to all modules without import overhead.
**Alternatives considered**:
- Tailwind CSS — Would require installing Tailwind, configuring PostCSS, rewriting all component styles. Massive scope expansion for a theming change.
- CSS-in-JS (styled-components / emotion) — Runtime overhead, new dependency, paradigm shift
- SCSS/Sass variables — Compile-time only, cannot be changed dynamically; adds build dependency

## R4: Hover-to-Edit Interaction Pattern

**Decision**: CSS `:hover` on section containers triggers visibility of edit icon; `onTouchStart` handles mobile
**Rationale**: Pure CSS hover detection is performant and avoids React re-renders for mouse tracking. The edit icon uses `opacity: 0` → `opacity: 1` transition on parent hover. For touch devices, a `onTouchStart` handler sets component state to show the icon, cleared on blur or after timeout.
**Alternatives considered**:
- `onMouseEnter`/`onMouseLeave` React handlers — Adds state updates on every hover, causing re-renders. CSS `:hover` is more efficient.
- Always-visible edit icons with reduced opacity — Violates the "looks like a resume" requirement; edit UI must be invisible at rest
- Intersection Observer — Over-engineered for this use case

## R5: Blinking Cursor Animation

**Decision**: Pure CSS `@keyframes` animation with `step-end` timing function
**Rationale**: A CSS-only approach has zero JavaScript overhead, works during React hydration, and is trivially simple. The `step-end` timing function produces an authentic terminal cursor blink (instant on/off, no fade).
**Alternatives considered**:
- `setInterval` in React — Unnecessary JavaScript; causes re-renders
- CSS `ease` transition — Produces a fade effect instead of a crisp terminal blink

## R6: Connect Page Declutter Strategy

**Decision**: Vertical single-column flow with progressive disclosure
**Rationale**: The current two-column layout (API keys | snippets) forces users to context-switch horizontally. A vertical flow guides users step-by-step: (1) generate key → (2) paste key → (3) choose assistant → (4) copy config. Config snippets collapse or fade when no key is pasted, reducing visual noise. The API key section becomes the hero area.
**Alternatives considered**:
- Stepper/wizard UI — Over-engineered for a 3-step flow; adds component complexity
- Keep two-column but reduce density — Still splits attention; doesn't solve the "which column first?" confusion
- Modal/drawer for config — Hides content too aggressively; users need to see the config in context

## R7: Replace window.prompt — Inline Form vs Modal

**Decision**: Inline form that expands within the resume list view
**Rationale**: An inline form keeps the user in context (they can see the list while naming the new version). It requires no overlay, z-index management, or scroll locking. It is consistent with the "no native dialogs" requirement and simpler to implement than a modal.
**Alternatives considered**:
- Styled modal dialog — Works but heavier implementation; user loses visual context of the list
- Slide-in drawer — Over-engineered for a single text input
- Popover anchored to button — Positioning edge cases on mobile; fragile
