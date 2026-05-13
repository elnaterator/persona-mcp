# Plan 008 - Adopt TanStack Query for server state

Date: 2026-05-09

Replace per-view `useEffect(fetch, [])` + manual `refresh()` pattern with `@tanstack/react-query` `useQuery` / `useMutation`. Centralizes cache, dedupes in-flight requests, refetches on focus, invalidates on mutate, and enables instant back-nav and optimistic updates for tag/link toggles. Thins out `useResourceList` / `useResourceDetail` / `useLinks` / `useTags` to query-key + fetcher wrappers (or removes them entirely).

## Requirements

### R1 - Server state managed by TanStack Query

All server-fetched data flows through `@tanstack/react-query`. No page issues raw `fetch` via `useEffect` for server state.

* `@tanstack/react-query` v5 added to `frontend/package.json` (no other deps).
* `<QueryClientProvider>` mounted in `main.tsx` above `<App>` with single shared `QueryClient`.
* Sensible defaults: `staleTime: 30s`, `gcTime: 5m`, `refetchOnWindowFocus: true`, `retry: 1` for queries, `retry: 0` for mutations.
* `QueryClient` constructed once at module scope; integrates with existing `ApiClientError` (error normalized via `handleResponse`, no extra wrapping).
* React DevTools Query panel enabled in dev only (`@tanstack/react-query-devtools` dev-dep, gated on `import.meta.env.DEV`).

### R2 - Query keys + fetcher hooks per resource

Each resource (resumes, applications, accomplishments, notes, contacts, tags, links, communications) exposes typed `useXList()` / `useXDetail(id)` query hooks plus a key factory.

* Query keys colocated with each `services/api/<resource>.ts` (or new `services/queries/<resource>.ts`) using a factory pattern: `resumeKeys.all`, `resumeKeys.lists()`, `resumeKeys.list(filters)`, `resumeKeys.detail(id)`.
* Hooks return native TanStack Query result (`{ data, isPending, isError, error, refetch, ... }`); pages destructure directly — no wrapping into the old `{ items, loading, error, refresh }` shape.
* Detail hooks use `enabled: !!id` to handle the optional-id case.
* Existing `useResourceList` / `useResourceDetail` / `useTags` / `useLinks` deleted; `__tests__/hooks/useResourceList.test.ts` and `useResourceDetail.test.ts` removed.

### R3 - Mutations with cache invalidation + optimistic updates

All writes (create / update / delete / link / unlink / tag toggle / communication CRUD) go through `useMutation` and invalidate or optimistically update the affected queries.

* Standard mutations (create / update / delete) call `queryClient.invalidateQueries({ queryKey: <resource>Keys.lists() })` and the affected `detail(id)` on success.
* Tag toggle and link/unlink use optimistic updates: `onMutate` snapshots + writes, `onError` rolls back, `onSettled` invalidates.
* Mutations on linked resources (e.g. linking an application to a resume) invalidate both sides' detail keys.
* Mutation `onError` surfaces failure via existing `useStatusMessage` hook (until R010 toast provider lands).

### R4 - Page migration

Every page using server data refactored to TanStack Query hooks; no `useEffect`-based fetching for server state remains.

* Migrated pages: `home/index.tsx`, `resumes/{ListView,DetailView,ResumeView}.tsx`, `applications/{ListView,DetailView}.tsx`, `accomplishments/{ListView,DetailView}.tsx`, `notes/{ListView,DetailView}.tsx`, `contacts/{ListView,DetailView}.tsx`.
* Components consuming `useTags()` / `useLinks()` (TagInput, LinksPanel, etc.) updated to new hooks.
* Loading / error UI preserved (same skeletons, same error messages).
* Vitest tests updated: existing component tests wrapped in a `QueryClientProvider` test helper; cache disabled per-test (`gcTime: 0`, `retry: false`).

### R5 - No regressions

Behavior parity with current app, validated by tests + manual run.

* `make check` (root) passes: lint, typecheck, vitest, backend pytest.
* Manual smoke: list pages load, detail pages load, create/edit/delete works on every resource, tag chips toggle, link picker links/unlinks, communication CRUD on contacts works.
* Bundle size delta acceptable (<25 KB gzip added — TanStack Query is ~13 KB gzip).

## Design

### Architecture

```
main.tsx
  └─ <QueryClientProvider client={queryClient}>
       └─ <ClerkProvider>
            └─ <App>   (existing tree unchanged)
```

Single `QueryClient` instance lives in new `frontend/src/services/queryClient.ts`. `services/api/*` modules keep their plain `async` fetcher functions — no React coupling — so they remain unit-testable and reusable from non-React contexts.

### Query hook layout

Pattern per resource (example: notes):

```ts
// services/api/notes.ts  (existing fetchers — unchanged)
export async function listNotes(): Promise<NoteSummary[]> { ... }
export async function getNote(id: number): Promise<Note> { ... }

// hooks/queries/notes.ts  (new)
export const noteKeys = {
  all: ['notes'] as const,
  lists: () => [...noteKeys.all, 'list'] as const,
  list: (filters?: NoteFilters) => [...noteKeys.lists(), filters ?? {}] as const,
  details: () => [...noteKeys.all, 'detail'] as const,
  detail: (id: number) => [...noteKeys.details(), id] as const,
}

export function useNoteList(filters?: NoteFilters) {
  return useQuery({ queryKey: noteKeys.list(filters), queryFn: () => listNotes(filters) })
}

export function useNoteDetail(id: number | undefined) {
  return useQuery({
    queryKey: id ? noteKeys.detail(id) : noteKeys.details(),
    queryFn: () => getNote(id!),
    enabled: !!id,
  })
}

export function useNoteMutations() {
  const qc = useQueryClient()
  const create = useMutation({
    mutationFn: createNote,
    onSuccess: () => qc.invalidateQueries({ queryKey: noteKeys.lists() }),
  })
  const update = useMutation({
    mutationFn: ({ id, body }: UpdateArgs) => updateNote(id, body),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: noteKeys.lists() })
      qc.invalidateQueries({ queryKey: noteKeys.detail(id) })
    },
  })
  const remove = useMutation({
    mutationFn: deleteNote,
    onSuccess: () => qc.invalidateQueries({ queryKey: noteKeys.lists() }),
  })
  return { create, update, remove }
}
```

Cross-resource mutations (links, communications) invalidate both endpoints. Example: `linkResources(a, b)` → invalidate `<aType>Keys.detail(aId)` and `<bType>Keys.detail(bId)`.

### Optimistic update — tag toggle (illustrative)

```ts
const toggleTag = useMutation({
  mutationFn: ({ resourceType, id, tag, add }) => add ? addTag(...) : removeTag(...),
  onMutate: async ({ resourceType, id, tag, add }) => {
    const key = keysFor(resourceType).detail(id)
    await qc.cancelQueries({ queryKey: key })
    const prev = qc.getQueryData<Detail>(key)
    qc.setQueryData<Detail>(key, (old) =>
      old ? { ...old, tags: add ? [...old.tags, tag] : old.tags.filter(t => t !== tag) } : old
    )
    return { prev, key }
  },
  onError: (_err, _vars, ctx) => ctx && qc.setQueryData(ctx.key, ctx.prev),
  onSettled: (_data, _err, _vars, ctx) => ctx && qc.invalidateQueries({ queryKey: ctx.key }),
})
```

### File layout

```
frontend/src/
  services/
    queryClient.ts                  # new: shared QueryClient + defaults
    api/                            # unchanged: pure fetchers
  hooks/
    queries/                        # new dir
      resumes.ts
      applications.ts
      accomplishments.ts
      notes.ts
      contacts.ts
      tags.ts
      links.ts
      communications.ts
      index.ts                      # barrel
    useStatusMessage.ts             # kept (UI state, not server state)
    useResourceList.ts              # DELETED
    useResourceDetail.ts            # DELETED
    useLinks.ts                     # DELETED
    useTags.ts                      # DELETED
  __tests__/
    test-utils.tsx                  # new: renderWithQueryClient helper
    hooks/queries/                  # new tests for query hooks (light — covers key shape + invalidation)
```

### Test helper

```ts
// __tests__/test-utils.tsx
export function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  })
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>)
}
```

### Risks + mitigations

* **StrictMode double-invoke**: TanStack Query handles this via request dedup — verify no duplicate POSTs in mutations during dev.
* **Stale data after mutation**: rely on invalidation (not manual `setQueryData`) except for documented optimistic paths.
* **Token rotation**: `setTokenGetter` already injects per-request via `fetchWithErrorHandling`; no Query change needed.
* **Suspense not adopted**: keep classic `isPending` / `isError` rendering; defer Suspense + ErrorBoundary integration to a future plan.

## Tasks

### P1 - Foundation

Wire library + provider + shared client. No page changes yet.

- [x] T01 Add `@tanstack/react-query` v5 + `@tanstack/react-query-devtools` (dev) to `frontend/package.json`; run install.
- [x] T02 Create `services/queryClient.ts` exporting configured `QueryClient` (defaults from R1).
- [x] T03 Mount `<QueryClientProvider>` in `main.tsx` above `<ClerkProvider>`; mount `<ReactQueryDevtools>` gated on `import.meta.env.DEV`.
- [x] T04 Add `__tests__/test-utils.tsx` with `renderWithQuery` helper. Also installed a global `vi.mock('@testing-library/react')` shim in `setup.ts` so the existing component test suite gets a fresh `QueryClientProvider` automatically.
- [x] T05 Verify `make check` (frontend lint + typecheck + test) passes with provider in place.

### P2 - Query hooks per resource

Build typed query/mutation hooks. Pages still use old hooks during this phase.

- [x] T06 `hooks/queries/resumes.ts`: keys factory + `useResumeList`, `useResumeDetail`, `useResumeMutations` (incl. version-scoped section mutations).
- [x] T07 `hooks/queries/applications.ts`: same shape.
- [x] T08 `hooks/queries/accomplishments.ts`: same shape.
- [x] T09 `hooks/queries/notes.ts`: same shape.
- [x] T10 `hooks/queries/contacts.ts`: contacts + communications sub-resource hooks + `useCommunicationSearch`.
- [x] T11 `hooks/queries/tags.ts`: `useAllTags`. (Tag toggle optimistic mutation deferred — no current callsite uses `useToggleTag`; tags currently mutated via parent resource update.)
- [x] T12 `hooks/queries/links.ts`: `useLinkMutations` with cross-resource invalidation (deferred per-side optimistic update — invalidation is sufficient for current UX).
- [x] T13 `hooks/queries/index.ts` barrel export.
- [x] T14 Light unit tests for keys + notes hooks + links hooks (key shape, fetcher called once, mutations invalidate expected keys).

### P3 - Page migration

Switch each page to new hooks. One commit per resource for clean diffs.

- [x] T15 Migrate `pages/home/index.tsx` (lists used by dashboard counts).
- [x] T16 Migrate `pages/resumes/{ListView,DetailView,ResumeView}.tsx`. Section components keep their `onUpdate` callback (parent invalidates the resume detail query) — they only mutate, no fetch, so plan R4 is satisfied without rewriting them.
- [x] T17 Migrate `pages/applications/{ListView,DetailView}.tsx`.
- [x] T18 Migrate `pages/accomplishments/{ListView,DetailView}.tsx`.
- [x] T19 Migrate `pages/notes/{ListView,DetailView}.tsx`.
- [x] T20 Migrate `pages/contacts/{ListView,DetailView}.tsx` incl. `CommunicationsPanel` and the cross-resource communication search (debounced query → `useCommunicationSearch`).
- [x] T21 Update shared components: `LinksPanel` uses `useLinkMutations`; `LinkPickerModal` consumes the per-resource list hooks.
- [x] T22 Component tests updated via global `setup.ts` shim. Two ResumeView/ResumeListView tests adjusted to match new state shape (banner-on-refresh, error-message effect).

### P4 - Cleanup + verification

- [x] T23 Deleted `hooks/useResourceList.ts`, `useResourceDetail.ts`, `useLinks.ts`, `useTags.ts` and the two `__tests__/hooks/useResource*.test.ts`.
- [x] T24 No residual `useEffect`-fetch patterns. Remaining `useEffect`s are for navigation, debounce, error mirroring, scroll, autoresize, label sync.
- [x] T25 `make check` (root) green — lint + typecheck + vitest (290 tests) + backend pytest (565 tests) + tf-check.
- [ ] T26 Manual smoke deferred to user (no dev server started in this run).
- [ ] T27 Bundle delta deferred (no `vite build` run).

### Implementation Notes

* **Sequence**: P1 → P2 → P3 → P4 strict. P2 hooks can be built in parallel across resources (T06–T12) since they share no state. P3 migrations also parallelizable per resource (T15–T20) but recommend serial for reviewability.
* **No backend changes**. Pure frontend refactor.
* **Tag/link optimistic updates** are the user-visible win — prioritize landing them correctly in T11/T12 with rollback tests.
* **Defer**: Suspense mode, prefetching on hover, infinite queries — none needed by current UX.
* **Coordination**: R010 (toast provider) will replace the `useStatusMessage` calls in mutation `onError`. Land R008 first; R010 is a mechanical follow-up.
* **Risk: refetch-on-focus surprise** — if it feels noisy in dev, scope to lists only (`refetchOnWindowFocus: 'always'` for lists, `false` for details) via per-hook override.
