# Plan 012 - Storybook + Playwright (shared components & e2e UI tests)

Date: 2026-05-23

Stand up two complementary UI quality tools. **Storybook** (react-vite builder) renders every shared primitive in `frontend/src/components/` in isolation, with a props/controls matrix and the a11y addon, enabling visual review and future visual-regression (Chromatic). **Playwright** drives the running app end-to-end to validate real behavior (golden-path CRUD per resource) and look-and-feel (targeted screenshots). Both are local-only tooling — **neither runs in the CI pipeline yet**.

## Requirements

### R1 - Storybook foundation

Storybook 8 installed against the existing Vite 6 + React 18 + TS 5.6 toolchain, sharing `vite.config.ts` resolution so CSS Modules and path aliases work without duplication.

* `@storybook/react-vite` ^8.x + `@storybook/addon-essentials` (controls, docs, viewport, backgrounds) + `@storybook/addon-a11y` added to `frontend` devDependencies; no production deps added.
* `frontend/.storybook/main.ts` configures the `react-vite` framework, `stories: ['../src/**/*.stories.@(tsx|mdx)']`, and the two addons.
* `frontend/.storybook/preview.tsx` imports `../src/index.css` so R009 design tokens (`--space-*`, `--color-*`, `--radius-*`, `--shadow-card`) resolve in every story; sets a dark background matching the app (`#1a1a1a`) as the default.
* Scripts: `"storybook": "storybook dev -p 6006"` and `"build-storybook": "storybook build"` added to `frontend/package.json`.
* `make storybook` target added to `frontend/Makefile` (alias for `npm run storybook`).
* `storybook-static/` added to `.gitignore`.
* `npm run build-storybook` exits 0 with zero broken stories.

### R2 - Global decorators + a11y

Components that depend on app context (Router, TanStack Query, Toast) render in Storybook via global decorators so individual stories stay declarative. The a11y addon reports violations per story.

* `frontend/.storybook/preview.tsx` wraps every story in a decorator stack: `MemoryRouter` (react-router v7), `QueryClientProvider` (a fresh `QueryClient` per story with retries off), and `ToastProvider`.
* Components needing Clerk (`Navigation`, `UserMenu`) either get a lightweight Clerk mock decorator or are explicitly out of scope for stories (documented in Implementation Notes) — do not pull a live `ClerkProvider` into Storybook.
* API-backed components (`LinkPickerModal`, `LinksPanel`, `CommunicationsPanel`) render with their data-fetching mocked at the `services/api` layer via a per-story decorator that seeds the QueryClient cache or stubs the api module — stories never hit a real backend.
* a11y addon active on all stories; zero serious/critical violations on presentational primitives (R3 set). Known exceptions documented inline with a story-level note.

### R3 - Component stories with props matrix

Each shared primitive has a `*.stories.tsx` colocated in `frontend/src/components/`, with a `Default` story plus stories covering the meaningful prop permutations.

* Stories authored (CSF3, `Meta` + typed `StoryObj`):
  * `Breadcrumb` — varying trail depth (1, 2, 3+ segments).
  * `ConfirmDialog` — default message + long message; `onConfirm`/`onCancel` wired to `fn()` actions.
  * `EditableSection` — view mode, edit mode, empty state.
  * `LinkPickerModal` — open with candidate list, empty candidates, pre-selected items (api mocked).
  * `TagInput` — empty, with existing tags, with `availableTags` suggestions, `allowCreate={false}`.
  * `LinksPanel` — zero links, mixed-type links, single-type (api/cache mocked).
  * `SectionCard` — with title + children, with action slot.
  * `LoadingSpinner` — default.
  * `FieldError` — with message, with no error (renders nothing).
  * `MarkdownContent` — headings/lists/code/links sample.
  * `AutoResizeTextarea` — empty, short, multi-line.
  * `InlineCreateForm` — collapsed, expanded, submitting state.
  * `EntryForm` — work/education/skill field configs (RHF + zod schema from R011).
  * `CommunicationsPanel` — empty, with communications (api mocked).
* Each story uses `argTypes` controls so reviewers can flip props live; `fn()` (`@storybook/test`) for callback args so the Actions panel logs interactions.
* `BlinkingCursor` story optional (trivial); include only if cheap.
* No story imports application pages — stories are component-scoped only.

### R4 - Playwright foundation (excluded from CI)

Playwright test runner installed and configured to drive a locally running app, explicitly kept out of the GitHub Actions pipeline.

* `@playwright/test` ^1.x added to `frontend` devDependencies; `npx playwright install chromium` documented in setup.
* `frontend/playwright.config.ts`: `testDir: './e2e'`, `baseURL: 'http://localhost:5173'`, `chromium` project (+ optional mobile viewport project for responsive checks), `reporter: 'html'`, traces/screenshots `on-first-retry`.
* `webServer` block starts the Vite dev server (`npm run dev`, reuse if already running) — the **backend + Clerk keys must already be running/configured**; documented as a precondition, not auto-started.
* Scripts: `"e2e": "playwright test"`, `"e2e:ui": "playwright test --ui"` in `frontend/package.json`; `make e2e` target in `frontend/Makefile`.
* `e2e/`, `playwright-report/`, `test-results/`, `e2e/.auth/` added to `.gitignore` where they are generated artifacts (keep `e2e/` source specs tracked; ignore only outputs + auth state).
* **CI guard**: no Playwright invocation added to `.github/workflows/`; the root `make check` and `frontend` `make check`/`make test` continue to run only lint + vitest (no e2e). Verified by grep of workflow files.

### R5 - Clerk authentication for e2e

e2e specs run as a real authenticated user using Clerk's official testing helpers, with the signed-in session captured once and reused.

* `@clerk/testing` ^1.x added to `frontend` devDependencies.
* `e2e/global.setup.ts` calls `clerkSetup()` then programmatically signs in a dedicated **test Clerk user** and writes `storageState` to `e2e/.auth/user.json`; the chromium project consumes that storage state so specs start authenticated.
* Required env vars documented in `frontend/.env.test.example`: `VITE_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `E2E_CLERK_USER_EMAIL`, `E2E_CLERK_USER_PASSWORD` (or a test-token flow). Secrets never committed.
* The test user is a real Clerk dev-instance user whose backend rows are isolated (its own `users` row per the 008-auth schema) so e2e data churn never touches a real account.
* `setupClerkTestingToken` used on page navigations to bypass Clerk bot protection on the dev instance.

### R6 - End-to-end behavior specs (golden paths)

One spec per resource area exercising the create → view → edit → delete loop through the real UI, asserting on user-visible outcomes.

* Specs under `e2e/`: `home.spec.ts`, `resumes.spec.ts`, `applications.spec.ts`, `accomplishments.spec.ts`, `notes.spec.ts`, `contacts.spec.ts`.
* Each CRUD spec: creates a record with a unique test-run marker in its name (e.g. `e2e-<timestamp>`), asserts it appears in the list, opens detail, edits a field and asserts persistence after reload, deletes it and asserts removal — then leaves no residue.
* Cross-cutting specs: navigation between sections via the header `Navigation`; tag add/remove on one resource (TagInput end-to-end); link add/remove via `LinkPickerModal` (LinksPanel reflects the change).
* Assertions target accessible roles/labels and visible text, not CSS-module class names (resilient to styling changes).
* Specs are independent and idempotent — each owns its data, runnable in any order, safe to re-run.

### R7 - Look-and-feel validation

Targeted visual checks guard the app's appearance without the flakiness of full-page pixel diffs.

* `toHaveScreenshot` baselines captured for stable, data-independent regions: header/`Navigation` bar, empty-state list pages, `ConfirmDialog`, a `SectionCard` shell.
* Dynamic content (timestamps, user-generated text, Clerk avatar) is masked via the `mask` option or excluded from the screenshot region to keep baselines stable.
* A mobile-viewport project re-runs the look-and-feel specs at a phone width to catch responsive breakage.
* Baselines committed under `e2e/__screenshots__/`; the plan documents that baseline refresh is a deliberate `--update-snapshots` step, run locally, reviewed in the diff.
* Because rendering varies across OSes, baselines are generated on one canonical environment (developer machine) and visual specs are tagged `@visual` so they can be skipped when run elsewhere — documented, not enforced in CI (R4).

## Design

### Storybook architecture

Storybook reuses the project's Vite config through `@storybook/react-vite`, so CSS Modules, TS paths, and the `@vitejs/plugin-react` transform behave identically to `npm run dev`. The only Storybook-specific wiring is the preview decorators and the token CSS import.

```ts
// frontend/.storybook/main.ts
import type { StorybookConfig } from '@storybook/react-vite'

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(tsx|mdx)'],
  addons: ['@storybook/addon-essentials', '@storybook/addon-a11y'],
  framework: { name: '@storybook/react-vite', options: {} },
}
export default config
```

```tsx
// frontend/.storybook/preview.tsx
import type { Preview } from '@storybook/react'
import { MemoryRouter } from 'react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastProvider } from '../src/components/toast'
import '../src/index.css'

const preview: Preview = {
  parameters: {
    backgrounds: { default: 'app', values: [{ name: 'app', value: '#1a1a1a' }] },
    a11y: { test: 'error' },
  },
  decorators: [
    (Story) => {
      const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
      return (
        <MemoryRouter>
          <QueryClientProvider client={qc}>
            <ToastProvider>
              <Story />
            </ToastProvider>
          </QueryClientProvider>
        </MemoryRouter>
      )
    },
  ],
}
export default preview
```

### Story pattern (CSF3)

```tsx
// frontend/src/components/TagInput.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { useState } from 'react'
import { fn } from '@storybook/test'
import { TagInput } from './TagInput'

const meta: Meta<typeof TagInput> = {
  title: 'Components/TagInput',
  component: TagInput,
  args: { availableTags: ['react', 'backend', 'urgent'], onChange: fn() },
}
export default meta
type Story = StoryObj<typeof TagInput>

export const Empty: Story = { args: { value: [] } }
export const WithTags: Story = { args: { value: ['react', 'urgent'] } }
export const NoCreate: Story = { args: { value: ['react'], allowCreate: false } }

// Interactive wrapper for controlled stories that need live state
export const Interactive: Story = {
  render: (args) => {
    const [tags, setTags] = useState<string[]>([])
    return <TagInput {...args} value={tags} onChange={setTags} />
  },
}
```

For API-backed components, a story-local decorator seeds the QueryClient cache or stubs the `services/api` module so no network call fires.

### Playwright architecture

```
running stack (precondition):
  backend  : localhost:8000  (make run-local, real Clerk-validated JWT, real Postgres/SQLite)
  frontend : localhost:5173  (vite dev, proxies /api → :8000)
        │
        ▼
playwright.config.ts
  ├─ globalSetup → e2e/global.setup.ts  (clerkSetup + sign in test user → storageState)
  ├─ project: chromium   (storageState: e2e/.auth/user.json)
  └─ project: mobile     (chromium, iPhone viewport, @visual specs)
        │
        ▼
e2e/*.spec.ts  → drive real UI, assert visible outcomes, self-clean data
```

```ts
// frontend/playwright.config.ts (sketch)
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/global.setup.ts',
  use: { baseURL: 'http://localhost:5173', trace: 'on-first-retry' },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], storageState: 'e2e/.auth/user.json' } },
    { name: 'mobile', use: { ...devices['iPhone 13'], storageState: 'e2e/.auth/user.json' } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,   // backend + Clerk env are a manual precondition
  },
  reporter: 'html',
})
```

### Clerk e2e auth flow

```ts
// e2e/global.setup.ts (sketch)
import { clerkSetup, clerk } from '@clerk/testing/playwright'
import { test as setup } from '@playwright/test'

setup('authenticate', async ({ page }) => {
  await clerkSetup()
  await page.goto('/')
  await clerk.signIn({
    page,
    signInParams: {
      strategy: 'password',
      identifier: process.env.E2E_CLERK_USER_EMAIL!,
      password: process.env.E2E_CLERK_USER_PASSWORD!,
    },
  })
  await page.context().storageState({ path: 'e2e/.auth/user.json' })
})
```

Specs reuse the captured session, so each spec opens already signed-in. `setupClerkTestingToken({ page })` is called in a `beforeEach` to defeat dev-instance bot protection.

### Directory layout

```
frontend/
  .storybook/
    main.ts                      # new
    preview.tsx                  # new
  src/components/
    *.stories.tsx                # new — one per shared primitive (R3)
  e2e/                           # new — tracked
    global.setup.ts              # new — Clerk auth → storageState
    home.spec.ts                 # new
    resumes.spec.ts              # new
    applications.spec.ts         # new
    accomplishments.spec.ts      # new
    notes.spec.ts                # new
    contacts.spec.ts             # new
    helpers/                     # new — selectors, unique-name factory, cleanup
    __screenshots__/             # new — committed visual baselines
    .auth/user.json              # gitignored — generated session
  .env.test.example              # new — required e2e env vars (no secrets)
  playwright.config.ts           # new
  package.json                   # scripts + devDeps
  Makefile                       # storybook + e2e targets
.gitignore                       # storybook-static, playwright-report, test-results, e2e/.auth
```

### CI boundary

R012 is explicitly **local-only tooling for now**. No workflow file under `.github/workflows/` invokes `storybook build` or `playwright test`. `make check` (root + frontend) is unchanged: lint + typecheck + vitest + backend pytest. A later plan can add a Storybook build job and/or a gated Playwright job once baselines prove stable.

### Risks

* **Clerk e2e brittleness**: programmatic sign-in against a live dev instance depends on Clerk's testing API and network. Mitigation: capture session once in `global.setup`, reuse via `storageState`; pin `@clerk/testing`. If password strategy is disabled on the instance, fall back to a Clerk testing-token + ticket flow.
* **e2e data residue**: specs create real rows in the dev DB. Mitigation: unique per-run markers + delete in the same spec; the test user is isolated (its own `users` row) so blast radius is contained. Consider a dedicated test DB before any CI promotion.
* **Visual-diff flakiness**: full-page screenshots vary by OS/font/Clerk render. Mitigation: snapshot only stable regions, `mask` dynamic content, tag `@visual`, generate baselines on one canonical machine. Do not gate CI on visuals in this plan.
* **Storybook + Clerk components**: `Navigation`/`UserMenu` need Clerk context. Mitigation: mock or exclude from stories; do not boot a real `ClerkProvider` in Storybook.
* **API-backed stories**: must not hit a backend. Mitigation: seed QueryClient cache or stub `services/api` per story; verify in `build-storybook` (offline).
* **Maintenance cost**: stories + e2e + baselines are code to maintain. Keep stories to genuine shared primitives; keep e2e to golden paths, not exhaustive matrices (that's vitest's job).

### Out of scope (future work)

* Chromatic / hosted visual-regression — defer (roadmap explicitly defers until shared set stabilizes).
* Playwright in CI — defer until auth + baselines proven; needs a seeded test DB + CI Clerk secrets.
* Cross-browser (Firefox/WebKit) projects — chromium only for now.
* Storybook interaction tests (`play` functions) beyond Actions logging — vitest + RTL already cover interaction logic.
* Stories for page-level views — component-scoped only.

## Tasks

### P1 - Storybook foundation

Install + configure; one trivial story proves the pipeline.

- [ ] T01 Add `@storybook/react-vite`, `@storybook/addon-essentials`, `@storybook/addon-a11y`, `@storybook/test` to `frontend` devDependencies; install.
- [ ] T02 Create `.storybook/main.ts` (react-vite framework, stories glob, two addons) per R1.
- [ ] T03 Create `.storybook/preview.tsx`: import `../src/index.css`, dark `app` background, decorator stack (MemoryRouter + QueryClient + ToastProvider) per R2.
- [ ] T04 Add `storybook` + `build-storybook` scripts to `package.json`; `make storybook` target; add `storybook-static/` to `.gitignore`.
- [ ] T05 Author one smoke story (`LoadingSpinner.stories.tsx`); run `npm run storybook` + `npm run build-storybook` — both green.

### P2 - Component stories

One story file per shared primitive (R3). Presentational first, provider/api-backed last.

- [ ] T06 Pure primitives: `Breadcrumb`, `ConfirmDialog`, `SectionCard`, `FieldError`, `MarkdownContent`, `AutoResizeTextarea` stories with prop permutations + `fn()` actions.
- [ ] T07 Stateful inputs: `TagInput` (empty/with-tags/suggestions/no-create + Interactive wrapper), `EditableSection` (view/edit/empty), `InlineCreateForm` (collapsed/expanded/submitting), `EntryForm` (work/education/skill configs with R011 schema).
- [ ] T08 API-backed: `LinkPickerModal`, `LinksPanel`, `CommunicationsPanel` — add per-story decorator that seeds QueryClient cache / stubs `services/api`; no network.
- [ ] T09 Decide + document Clerk-dependent (`Navigation`, `UserMenu`): mock decorator or exclude; note in Implementation Notes.
- [ ] T10 Run a11y addon across all stories; resolve serious/critical violations or annotate documented exceptions. `build-storybook` green offline.

### P3 - Playwright foundation + auth

Runner, config, Clerk session capture. No specs yet beyond an auth smoke.

- [ ] T11 Add `@playwright/test` + `@clerk/testing` to devDependencies; document `npx playwright install chromium`.
- [ ] T12 Create `playwright.config.ts` (testDir `e2e`, baseURL, chromium + mobile projects, webServer reuse, html reporter) per R4.
- [ ] T13 Create `e2e/global.setup.ts`: `clerkSetup` + programmatic sign-in → `e2e/.auth/user.json`; wire `globalSetup` + project `storageState`.
- [ ] T14 Create `frontend/.env.test.example` with required vars; add `e2e/.auth`, `playwright-report/`, `test-results/` to `.gitignore`.
- [ ] T15 Auth smoke spec: navigate `/`, assert signed-in header (`Navigation` visible, no landing page). `make e2e` green against locally running stack.

### P4 - e2e behavior + look-and-feel specs

Golden-path CRUD per resource + targeted visual baselines.

- [ ] T16 `e2e/helpers/`: unique-name factory (`e2e-<timestamp>`), shared selectors (roles/labels), cleanup utility.
- [ ] T17 CRUD specs `resumes`, `applications`, `accomplishments`, `notes`, `contacts`: create → list-assert → detail edit → reload-assert → delete → absent. Self-cleaning, independent.
- [ ] T18 Cross-cutting specs: header navigation across sections; TagInput add/remove end-to-end; LinkPickerModal add/remove reflected in LinksPanel.
- [ ] T19 Look-and-feel `@visual` specs (R7): `toHaveScreenshot` for header, empty-state list, ConfirmDialog, SectionCard; mask dynamic content; commit baselines under `e2e/__screenshots__/`.
- [ ] T20 Re-run `@visual` specs under the mobile project; commit mobile baselines; confirm responsive layout intact.

### P5 - Verification + docs

- [ ] T21 Grep `.github/workflows/` — confirm no `storybook`/`playwright` invocation (R4 CI guard). `make check` (root) unchanged + green.
- [ ] T22 README/AGENTS note: how to run Storybook (`make storybook`), how to run e2e (preconditions: backend + Clerk env, `npx playwright install`, `make e2e`), how to refresh visual baselines (`--update-snapshots`).
- [ ] T23 Full local pass: `build-storybook` offline green; `make e2e` green (CRUD + visual) against `make run-local` stack; html report reviewed.

### Implementation Notes

* **Sequence**: P1 → P2 are independent of P3 → P4 (Storybook vs Playwright are separate tools). Parallelizable across two tracks; P5 closes both. Within P2, T06 (pure) before T08 (api-backed) so the decorator pattern is proven on easy cases first.
* **Reuse the Vite config**: do not fork build settings into Storybook — `@storybook/react-vite` inherits `vite.config.ts`. The only new config is `.storybook/preview.tsx` decorators + token CSS import.
* **Decorator over per-story boilerplate**: Router/Query/Toast live in the global decorator; only api stubbing is per-story (since cache contents differ).
* **e2e is local-only this plan**: keep every Playwright invocation out of CI. The CI guard (T21) is a hard acceptance criterion, not a nicety.
* **Test user isolation**: the e2e Clerk user must be a throwaway dev-instance account; its backend `users` row keeps churn off any real data. Never point e2e at a production Clerk instance or prod DB.
* **Assert on accessibility, not classes**: e2e + a11y both push toward role/label-based queries — this keeps tests resilient to the R009 token / CSS-module churn that other roadmap items cause.
* **Keep scope honest**: stories cover shared primitives only; e2e covers golden paths only. Exhaustive prop/branch coverage stays in vitest (R already green). Don't duplicate unit coverage in slow e2e.
* **Visual baselines are environment-bound**: generate on one canonical machine; treat a baseline refresh as a reviewed diff, never an unattended `--update-snapshots` in scripts.
