# Quickstart: 014 UX Overhaul

## Prerequisites

- Node.js 18+ and npm
- The frontend dev server (`cd frontend && make run`)

## Setup

```bash
# From the feature branch
cd frontend

# Install the new dependency
npm install lucide-react

# Start dev server with HMR
npm run dev
```

## Development Workflow

This is a frontend-only feature. All work happens in `frontend/src/`.

### 1. Theme Foundation (Start Here)

Edit `frontend/src/index.css` to define CSS custom properties on `:root` and apply dark theme base styles. Every subsequent CSS module change references these variables.

### 2. Component-by-Component

Each component's `.module.css` file is rewritten to use `var(--variable-name)` references and remove rounded corners. Work through components in priority order:

1. `index.css` → global theme
2. `Navigation` → icons, Connect highlighting
3. `ConnectView` → decluttered layout
4. `EditableSection` → hover-to-edit behavior
5. Resume sections (Contact, Summary, Experience, Education, Skills) → resume layout
6. `ResumeListView` + `InlineCreateForm` → replace window.prompt
7. Remaining views (Applications, Accomplishments, Notes) → dark theme pass

### 3. Running Tests

```bash
cd frontend
make test       # Run Vitest
make lint        # Run ESLint
make check       # Both
```

### 4. Verifying Changes

```bash
# Full stack (frontend build + backend serve)
cd /path/to/repo
make run-local

# Or frontend dev server only
cd frontend
npm run dev
```

Open `http://localhost:5173` (dev) or `http://localhost:8000` (run-local).

## Key Files

| File | Purpose |
|------|---------|
| `src/index.css` | CSS custom properties, global dark theme |
| `src/components/Navigation.tsx` | Tab icons, Connect highlighting |
| `src/components/ConnectView/index.tsx` | Decluttered Connect page |
| `src/components/EditableSection.tsx` | Hover-to-edit wrapper |
| `src/components/ResumeDetailView.tsx` | Resume-like layout |
| `src/components/InlineCreateForm.tsx` | New — replaces window.prompt |
| `src/components/BlinkingCursor.tsx` | New — green cursor accent |
| `src/router.tsx` | Default route change (/ → /connect) |
