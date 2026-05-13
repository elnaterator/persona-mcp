# Plan 010 - Toast / notification provider

Date: 2026-05-12

Replace the mix of per-view `useStatusMessage()` hooks and ad-hoc `useState<{type, message}>()` patterns with a single root-mounted `<ToastProvider>` + `useToast()` hook. One render slot, queued display, animated enter/exit, no prop drilling, no per-view timers. Cuts ~10 LOC per list/detail view and unblocks R008 mutation `onError` paths from depending on local component state.

## Requirements

### R1 - Single global toast provider

One `<ToastProvider>` mounted once at the app root renders all toasts in a fixed-position container. No view renders its own `<StatusMessage>`.

* `<ToastProvider>` mounted in `main.tsx` (or `App.tsx`) inside `<QueryClientProvider>` so mutation callbacks can call `useToast()` from any hook depth.
* Fixed-position container (top-right desktop, top-center mobile) renders the queue; container is the only DOM home for toasts.
* `aria-live="polite"` on success toasts, `aria-live="assertive"` on error toasts; `role="status"` / `role="alert"` matched accordingly.
* Container is keyboard-accessible: `Esc` dismisses the focused toast; toasts focusable via `Tab` only when persistent (no auto-dismiss).
* Reuses existing color tokens (`--status-success`, `--status-error`, `--status-warning`) — no new design tokens required beyond R009.

### R2 - `useToast()` hook API

A typed hook exposes the imperative API used by every page and mutation handler.

* `useToast()` returns `{ toast, success, error, warning, dismiss, dismissAll }`.
* `success(message, opts?)` / `error(...)` / `warning(...)` are sugar over `toast({ type, message, ...opts })`; both signatures supported.
* `opts`: `{ duration?: number; id?: string; action?: { label: string; onClick: () => void } }`. Default duration: 3000ms for success/warning, 5000ms for error, `Infinity` for persistent.
* `toast(...)` returns the toast id; callers can `dismiss(id)` to clear early (used by optimistic mutation rollback flows).
* Re-calling with the same `id` replaces the existing toast in place (no flicker) — needed for mutation lifecycle: "Saving…" → "Saved".
* Type-safe: `useToast` throws (dev only) if called outside the provider.

### R3 - Queue + animation behavior

Multiple concurrent toasts queue and animate cleanly; nothing pops in/out abruptly.

* Max 3 simultaneous toasts; older ones evict on overflow (FIFO).
* Enter: 150ms fade + 8px translateY; exit: 150ms fade. Reduced-motion (`prefers-reduced-motion: reduce`) disables transform but keeps opacity fade.
* Pause auto-dismiss timer on hover/focus; resume on leave.
* Stack vertically with `--space-2` gap (R009 token).
* Optional inline action button (`action.label`) inside the toast invokes `action.onClick` then dismisses.

### R4 - Migration — all status surfaces moved to toasts

Every existing `StatusMessage` / `useStatusMessage` / local status `useState` is replaced with `useToast()` calls.

* Migrated pages: `resumes/{ListView,DetailView,ResumeView,ExperienceSection,SkillsSection,EducationSection}.tsx`, `applications/{ListView,DetailView}.tsx`, `accomplishments/DetailView.tsx`, `notes/DetailView.tsx`, `contacts/DetailView.tsx`.
* Migrated components: `EditableSection.tsx`, `CommunicationsPanel.tsx` (both currently render their own `<StatusMessage>` inline).
* Inline error banners that are *not* transient (e.g., "Failed to load — Retry") stay as inline UI — toasts are for transient feedback only. Distinguish in PR description with a list.
* R008 TanStack Query mutation `onError` callbacks (where wired) updated to call `useToast().error(...)` directly — replaces the temporary `useStatusMessage` indirection noted in plan 008.

### R5 - Cleanup + no regressions

Old hook + component deleted; nothing left to drift.

* `frontend/src/hooks/useStatusMessage.ts` and `__tests__/hooks/useStatusMessage.test.ts` deleted.
* `frontend/src/components/StatusMessage.tsx` + `.module.css` deleted (toast renders its own markup; no shared surface).
* `make check` (root) green.
* Manual smoke: trigger success + error toasts on every migrated page; verify queueing by triggering 4+ in a row; verify hover-pause; verify reduced-motion via DevTools emulation.
* Bundle size delta < +3 KB gzip (no new deps — built in-house).

## Design

### Provider sketch

```tsx
// components/toast/ToastProvider.tsx
type ToastType = 'success' | 'error' | 'warning'
type Toast = {
  id: string
  type: ToastType
  message: string
  duration: number
  action?: { label: string; onClick: () => void }
  createdAt: number
}

const ToastContext = createContext<ToastApi | null>(null)

export function ToastProvider({ children, max = 3 }: Props) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts((q) => q.filter((t) => t.id !== id))
  }, [])

  const toast = useCallback((input: ToastInput): string => {
    const id = input.id ?? crypto.randomUUID()
    setToasts((q) => {
      const existing = q.findIndex((t) => t.id === id)
      const next: Toast = { id, createdAt: Date.now(), duration: defaultDuration(input.type), ...input }
      if (existing >= 0) {
        const copy = [...q]; copy[existing] = next; return copy
      }
      const trimmed = q.length >= max ? q.slice(1) : q
      return [...trimmed, next]
    })
    return id
  }, [max])

  const api = useMemo<ToastApi>(() => ({
    toast,
    success: (m, o) => toast({ type: 'success', message: m, ...o }),
    error:   (m, o) => toast({ type: 'error',   message: m, ...o }),
    warning: (m, o) => toast({ type: 'warning', message: m, ...o }),
    dismiss,
    dismissAll: () => setToasts([]),
  }), [toast, dismiss])

  return (
    <ToastContext.Provider value={api}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within <ToastProvider>')
  return ctx
}
```

### Container + item

`<ToastContainer>` is a portal-free fixed-position `<ol>` rendered as the provider's last child. `<ToastItem>` owns its own dismiss timer in a `useEffect` (cleared on unmount, paused via `onMouseEnter` / `onFocus`). Enter/exit transitions implemented with a `data-state="entering|visible|leaving"` attribute + CSS `transition`, no animation library.

### File layout

```
frontend/src/
  components/
    toast/
      ToastProvider.tsx      # new — context + state + API
      ToastContainer.tsx     # new — fixed-position list
      ToastItem.tsx          # new — individual toast + timer
      Toast.module.css       # new — uses R009 tokens
      index.ts               # new — barrel: ToastProvider, useToast
    StatusMessage.tsx        # DELETED in P3
    StatusMessage.module.css # DELETED in P3
  hooks/
    useStatusMessage.ts      # DELETED in P3
  __tests__/
    hooks/useStatusMessage.test.ts  # DELETED in P3
    components/toast/         # new — provider + queue behavior tests
```

### Mutation lifecycle pattern (cookbook)

```ts
const { success, error } = useToast()
const create = useMutation({
  mutationFn: createNote,
  onMutate: () => toast({ id: 'note-save', type: 'success', message: 'Saving…', duration: Infinity }),
  onSuccess: () => success('Saved', { id: 'note-save' }),
  onError:   (e) => error(e.message, { id: 'note-save' }),
})
```

### Accessibility

* Container `<ol role="region" aria-label="Notifications">`.
* Each item: `role="status"` (success/warning) or `role="alert"` (error), `aria-atomic="true"`.
* Dismiss button: `aria-label="Dismiss notification"`.
* Toasts do not steal focus; sighted keyboard users discover them via a separate `aria-keyshortcuts` hint or simply by `Tab` order (container near end of DOM).

### Risks

* **Toast spam from mutation retries**: TanStack Query retries fire `onError` once per final failure (not per attempt) with default `retry: 1`; verify no double-toast in dev.
* **SSR-unsafe `crypto.randomUUID`**: app is pure SPA, no SSR — safe; if SSR ever lands, swap to a counter.
* **Provider above `<QueryClientProvider>` vs below**: place *inside* `<QueryClientProvider>` so query hooks remain unaware; place *outside* `<ClerkProvider>` only if Clerk needs toasts (it doesn't — keep it inside both).
* **Test flake from real timers**: tests use `vi.useFakeTimers()` + `vi.advanceTimersByTime()` for auto-dismiss assertions.

## Tasks

### P1 - Provider + primitives

Build the provider standalone; no migration yet.

- [x] T01 Create `components/toast/ToastProvider.tsx` with context, queue, FIFO eviction (max 3), `toast` / `success` / `error` / `warning` / `dismiss` / `dismissAll` API per R2.
- [x] T02 Create `components/toast/ToastContainer.tsx` — fixed-position `<ol>`, top-right desktop / top-center mobile (CSS media query, R009 tokens).
- [x] T03 Create `components/toast/ToastItem.tsx` — auto-dismiss timer, hover/focus pause, enter/exit animation via `data-state` attribute, optional action button.
- [x] T04 Create `components/toast/Toast.module.css` using R009 tokens only (`--space-*`, `--radius-md`, `--shadow-card`, `--status-*`); honor `prefers-reduced-motion`.
- [x] T05 Create `components/toast/index.ts` barrel exporting `ToastProvider` and `useToast`.
- [x] T06 Mount `<ToastProvider>` in `main.tsx` inside `<QueryClientProvider>` and inside `<ClerkProvider>`.

### P2 - Migrate consumers

Replace every old status surface. One commit per resource area for clean diffs.

- [x] T07 Migrate `pages/resumes/*.tsx` (ListView, DetailView, ResumeView, ExperienceSection, SkillsSection, EducationSection).
- [x] T08 Migrate `pages/applications/*.tsx` (ListView, DetailView).
- [x] T09 Migrate `pages/accomplishments/AccomplishmentDetailView.tsx`.
- [x] T10 Migrate `pages/notes/NoteDetailView.tsx`.
- [x] T11 Migrate `pages/contacts/ContactDetailView.tsx`.
- [x] T12 Migrate shared `components/EditableSection.tsx` and `components/CommunicationsPanel.tsx` (drop their internal `<StatusMessage>` usage; emit toasts instead).
- [x] T13 If R008 landed: update mutation `onError` callbacks across `hooks/queries/*.ts` to call `useToast().error(...)` via a small `useMutationToast` helper (or per-call sites — pick whichever stays simpler). (N/A — no onError callbacks in query files; error handling done inline in page components.)

### P3 - Cleanup + verification

- [x] T14 Delete `components/StatusMessage.tsx`, `components/StatusMessage.module.css`, `hooks/useStatusMessage.ts`, `__tests__/hooks/useStatusMessage.test.ts`.
- [x] T15 Grep `frontend/src` for residual `StatusMessage` / `useStatusMessage` / local `status*` `useState` patterns; resolve holdouts. (`statusFilter` in ApplicationListView is a filter field, not a status message — clean.)
- [x] T16 Add `__tests__/components/toast/` tests: queue eviction at max=3, hover-pause auto-dismiss, same-id replace-in-place, `dismiss` removes correct item, reduced-motion path skips transform.
- [x] T17 Run `make check` (root) — lint + typecheck + vitest + backend pytest green. (281 frontend + 565 backend, lint clean.)
- [x] T18 Manual smoke per R5 across all migrated pages incl. queue overflow + hover-pause + reduced-motion DevTools toggle.
- [x] T19 Measure prod bundle size before/after; record delta in PR description.

### Implementation Notes

* **Sequence**: P1 → P2 → P3 strict. Within P2 (T07–T12) parallelizable but recommend serial for reviewability.
* **No new deps**. In-house provider keeps bundle lean and avoids `react-hot-toast` / `sonner` opinions on positioning + a11y.
* **Coordination with R008**: if R008 lands first, T13 picks up the `useStatusMessage` temporary indirection it left behind. If R010 lands first, R008's mutation `onError` writes call `useToast().error(...)` from day one — even simpler.
* **Coordination with R012 (Storybook)**: write the toast stories at the same time (success / error / warning / action / queue overflow). Defer if Storybook not yet set up.
* **Inline action toasts** (e.g., "Note deleted — Undo") are supported by the API but only wired when a specific UX calls for them — no speculative undo implementations in this plan.
* **Persistent toasts** (`duration: Infinity`) are used by long-running mutation patterns (T13 cookbook); document this clearly in the toast README/comment so future contributors don't recreate it.
