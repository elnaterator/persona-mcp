# Plan 006 - Frontend Refactor: Pages + Shared Components

Date: 2026-05-04

Reorganize `frontend/src/` into `pages/` (one subdir per route) + top-level `components/` (shared). Split monolithic `types/resume.ts` (238 LOC, all types) and `services/api.ts` (963 LOC, all endpoints) per resource. Extract reusable hooks. Update `AGENTS.md`.


## Requirements

### R1 - Pages directory structure

`frontend/src/pages/<page>/` houses page-specific code. Each page owns its list, detail, and subcomponents not shared across pages.

* `pages/` dir created at `frontend/src/pages/`
* Subdirs: `home/`, `resumes/`, `applications/`, `accomplishments/`, `notes/`, `contacts/`
* Each subdir contains list view, detail view, and page-only subcomponents + their CSS modules + colocated tests
* `router.tsx` imports updated to new paths
* No page imports another page's internal subcomponent (only shared components)
* All existing functionality unchanged (visual + behavior parity)


### R2 - Shared components directory

Top-level `frontend/src/components/` only contains components reused across ≥2 pages or page-agnostic primitives.

* Shared list (stays in `components/`): `AutoResizeTextarea`, `BlinkingCursor`, `Breadcrumb`, `ConfirmDialog`, `EditableSection`, `EntryForm`, `InlineCreateForm`, `LinkPickerModal`, `LinksPanel`, `LinkCountBadge`, `LoadingSpinner`, `MarkdownContent`, `Navigation`, `NotFound`, `SectionCard`, `StatusMessage`, `TagInput`, `CommunicationsPanel`, `ContactsPanel`, `AuthGuard/`, `UserMenu/`, `LandingPage/`
* Resume-specific sections (`ContactSection`, `ExperienceSection`, `EducationSection`, `SkillsSection`, `SummarySection`, `ResumeView`) → `pages/resumes/`
* `HomeView/` → `pages/home/`
* Tests at `frontend/src/__tests__/` mirror new layout (or colocate next to component — pick one and apply consistently)


### R3 - Split `types/resume.ts`

Misnamed (holds all types). Split per resource into a `types/` barrel.

* `types/` files: `resume.ts` (Resume, ContactInfo, WorkExperience, Education, Skill, ResumeVersion*), `application.ts`, `accomplishment.ts`, `note.ts`, `contact.ts`, `communication.ts`, `link.ts` (ResourceRef, ResourceType, GroupedLinks), `api.ts` (ApiError, ApiValidationError, ApiSuccessResponse), `tag.ts`
* `types/index.ts` barrel re-exports everything
* All consumers import from `'../types'` (or `@/types` if path alias added) — no deep imports into individual files
* `resume.ts` filename retained but only resume-shape types remain


### R4 - Split `services/api.ts`

963 LOC monolith. Split per resource for navigability.

* `services/api/` dir: `client.ts` (fetch wrapper, `setTokenGetter`, `API_BASE`, error parsing), `resumes.ts`, `applications.ts`, `accomplishments.ts`, `notes.ts`, `contacts.ts`, `communications.ts`, `links.ts`, `tags.ts`, `index.ts` (barrel)
* Public API surface unchanged — same exported function names from `services/api`
* Each module imports shared `client` helpers, exports its endpoint funcs


### R5 - Reusable hooks

Extract repeated patterns from list/detail views into `frontend/src/hooks/`.

* `useResourceList<T>(fetcher)` — loading/error/refresh state for list pages
* `useResourceDetail<T>(id, fetcher)` — same for detail pages
* `useStatusMessage()` — wrap StatusMessage show/clear/auto-dismiss
* `useLinks(resourceType, id)` — fetch + group linked resources (used by every detail page)
* `useTags()` — tag pool fetch + autocomplete
* Migrate at minimum 2 list views + 2 detail views to hooks to validate API; document remaining as follow-up


### R6 - AGENTS.md doc update

`AGENTS.md` "Project Layout" section reflects new structure.

* `frontend/src/` tree under "Project Layout" updated: `pages/`, `components/`, `hooks/`, `services/api/`, `types/`
* One-paragraph "Frontend Organization" subsection: page-vs-shared rule, when to add to `pages/` vs `components/`, types/services barrel pattern
* CLAUDE.md unchanged (auto-includes AGENTS.md)


### R7 - Verification

* `make check` (frontend) green: ESLint + Vitest + tsc
* All existing tests pass post-move (paths updated, no behavior change)
* Manual smoke: every route loads, CRUD works, links + tags + comms unchanged


## Design

**Target tree:**

```
frontend/src/
  pages/
    home/                  index.tsx, *.module.css
    resumes/               ListView, DetailView, ResumeView,
                           ContactSection, ExperienceSection,
                           EducationSection, SkillsSection, SummarySection
    applications/          ListView, DetailView
    accomplishments/       ListView, DetailView
    notes/                 ListView, DetailView
    contacts/              ListView, DetailView
  components/              shared primitives (see R2)
  hooks/                   useResourceList, useResourceDetail,
                           useStatusMessage, useLinks, useTags
  services/
    api/
      client.ts            fetch + auth + error
      resumes.ts ...        per-resource endpoints
      index.ts             barrel
  types/
    resume.ts application.ts accomplishment.ts note.ts contact.ts
    communication.ts link.ts tag.ts api.ts index.ts
  router.tsx App.tsx main.tsx index.css
```

**Page-vs-shared rule:** component used in exactly one page → page subdir; used in ≥2 pages OR is a UI primitive (button-like, dialog, form input) → `components/`.

**Test colocation:** keep tests in `__tests__/` mirror tree (lower churn, matches current convention). Update test imports only.

**Path alias (optional, recommended):** add `@/` → `src/` in `tsconfig.json` + `vite.config.ts` to avoid `../../../` after restructure. If declined, use relative imports.

**Backwards compat:** none required, no external consumers of `frontend/src/`. Single PR, atomic.

**Other high-value refactors suggested (defer to follow-up plans, don't do here):**
- Toast/notification provider replacing per-view `StatusMessage` state
- Form abstraction (zod + react-hook-form) — current `EntryForm` is bespoke
- React Query / TanStack Query for server state caching (replaces ad-hoc useEffect fetchers + manual refresh)
- Theme tokens in CSS (`:root` vars) for spacing/colors — many `.module.css` files duplicate values
- Storybook for shared `components/` visual review


## Tasks

### P1 - Type + service split (foundation, no UI churn)

Split first so page moves only touch import paths once.

- [x] T01 Create `types/` per-resource files; move types from `resume.ts`; add `types/index.ts` barrel
- [x] T02 Update all import sites to `from '../types'` (or alias)
- [x] T03 Create `services/api/client.ts` (fetch wrapper, auth, error) extracted from `services/api.ts`
- [x] T04 Create per-resource service files; move endpoint funcs; `services/api/index.ts` barrel
- [x] T05 Delete old monolithic `services/api.ts`; update imports
- [x] T06 Run `make check` — fix any TS/lint breakage


### P2 - Pages reorganization

Move page-specific files into `pages/<name>/` subdirs.

- [x] T07 Create `pages/` dir; add `home/`, `resumes/`, `applications/`, `accomplishments/`, `notes/`, `contacts/` subdirs
- [x] T08 Move `HomeView/` → `pages/home/`
- [x] T09 Move resume files (ListView, DetailView, ResumeView, *Section) → `pages/resumes/`
- [x] T10 Move ApplicationListView, ApplicationDetailView (+ css) → `pages/applications/`
- [x] T11 Move AccomplishmentListView, AccomplishmentDetailView → `pages/accomplishments/`
- [x] T12 Move NoteListView, NoteDetailView → `pages/notes/`
- [x] T13 Move ContactListView, ContactDetailView → `pages/contacts/`
- [x] T14 Update `router.tsx` imports
- [x] T15 Update `__tests__/` import paths to new locations
- [x] T16 Verify `components/` only contains shared (R2 list); enforce by review
- [x] T17 Run `make check` — green


### P3 - Hooks extraction

Pull reusable state patterns into `hooks/`.

- [x] T18 `hooks/useResourceList.ts` + tests
- [x] T19 `hooks/useResourceDetail.ts` + tests
- [x] T20 `hooks/useStatusMessage.ts` + tests
- [x] T21 `hooks/useLinks.ts` (wrap existing LinksPanel fetch logic)
- [x] T22 `hooks/useTags.ts`
- [x] T23 Migrate 2 list views (e.g. NoteListView, ContactListView) to `useResourceList`
- [x] T24 Migrate 2 detail views to `useResourceDetail` + `useLinks`
- [x] T25 Run `make check`


### P4 - Docs + final verify

- [x] T26 Update `AGENTS.md` Project Layout section + add Frontend Organization paragraph
- [x] T27 (skipped — path alias deferred)
- [x] T28 (deferred — requires running dev server manually)
- [x] T29 Final make check — passes


### Implementation Notes

- **Order matters:** P1 before P2 — splitting types/services first means page moves are pure file relocations, not edits-in-place.
- **One PR, atomic.** Diff is large but mechanical. Reviewers should `git mv` the files for clean rename detection (`git mv` → minimal diff on file content).
- **`git mv` everywhere** — preserves blame.
- **No behavior changes in P1+P2.** Hooks (P3) are the only behavior-touching phase; gated by tests.
- **Skip path alias (T27) if Vite/tsconfig config drift becomes a tarpit.** Relative imports work fine.
- **Parallel:** P3 tasks T18–T22 are independent of each other. T23–T24 sequential after them.
- **Watch for:** circular imports when splitting `types/` (link.ts may reference all resource types — keep `ResourceType` enum in `link.ts`, import where needed).
- **Out of scope (suggest follow-ups in PR description):** toast provider, form abstraction, React Query, theme tokens, Storybook.
