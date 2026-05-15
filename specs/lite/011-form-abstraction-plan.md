# Plan 011 - Form abstraction (react-hook-form + zod)

Date: 2026-05-12

Replace hand-rolled `useState` field state + ad-hoc `.trim()` validation across `EntryForm`, `InlineCreateForm`, `CommunicationsPanel`, every page-level create/edit form (`ContactListView`, `ContactDetailView`, `ApplicationListView`, `ApplicationDetailView`, `AccomplishmentListView`, `AccomplishmentDetailView`, `NoteListView`, `NoteDetailView`, `ResumeDetailView`, `SummarySection`, `ContactSection`, `ExperienceSection`, `EducationSection`, `SkillsSection`) with `react-hook-form` (uncontrolled inputs, fast re-renders) + `zod` schemas (single source of truth, inferred TS types). Kills validation drift between client + backend Pydantic models. As part of the same change, **unify the create and edit form UI** for accomplishments, notes, and contacts by extracting one shared per-resource form component used by both the list-page create flow and the detail-page edit flow — the existing edit layout (`fieldRow` / `fieldGroup` grid) becomes the canonical layout; the divergent list-page `newForm` grids are deleted.

## Requirements

### R1 - Dependencies + provider-free wiring

`react-hook-form` v7 + `zod` v3 + `@hookform/resolvers` added; no global provider required (`useForm` is self-contained).

* `react-hook-form` ^7.x, `zod` ^3.x, `@hookform/resolvers` ^3.x added to `frontend/package.json` (production deps).
* No app-level provider mount — each form's component owns its `useForm()` instance.
* Bundle budget: < +18 KB gzip combined (RHF ~9 KB, zod ~12 KB tree-shaken). Record actual delta in PR.
* `tsconfig` `strict` already on — verify `zod` inferred types flow through `SubmitHandler<z.infer<typeof schema>>` without `any`.

### R2 - Schema module per resource

Each backend resource has one zod schema module that mirrors the Pydantic model's required fields and validation rules. Schemas live next to the typed API, not next to individual forms.

* New `frontend/src/schemas/` directory with one file per resource: `contact.ts`, `application.ts`, `accomplishment.ts`, `note.ts`, `resume.ts`, `communication.ts`, `resumeEntry.ts` (work/education/skill/summary/contactInfo sub-schemas).
* Each schema exports `xxxCreateSchema`, `xxxUpdateSchema` (often `.partial()` of create), and `type XxxCreateInput = z.infer<typeof xxxCreateSchema>`.
* Validation rules match backend Pydantic: required strings use `.min(1, 'Required')`, URLs use `.url()`, emails use `.email()`, dates use `.regex(/^\d{4}-\d{2}-\d{2}$/)` matching the date format the backend accepts.
* Trim transforms applied via `.trim()` on strings before length validation (`z.string().trim().min(1)`).
* Empty-string optional fields normalized to `undefined` via `.transform((v) => v || undefined).optional()` so the API receives `null`/omitted instead of `""`.
* `__tests__/schemas/<resource>.test.ts` covers happy path + each validation rule.

### R3 - `EntryForm` rebuilt on RHF

Shared `EntryForm` becomes a thin RHF wrapper accepting a `zodResolver` schema; `FieldConfig` retained for declarative field rendering.

* `EntryForm` props gain `schema: ZodSchema` (replaces ad-hoc validation in current `validate()` function).
* Internal `useState<formData>` + `useState<errors>` removed; replaced by `useForm({ resolver: zodResolver(schema), defaultValues, mode: 'onBlur' })`.
* `highlights` (string[]) field uses `useFieldArray` for add/remove/reorder; current manual splice logic deleted.
* Existing call sites (resume section forms) pass per-section schema; no behavior change visible to user beyond consistent error formatting.
* Existing `__tests__/components/EntryForm.test.tsx` updated to assert zod error messages render in DOM.

### R4 - Page-level forms migrated

Every page or component currently doing `useState<form>` + manual `.trim()` validation uses `useForm()` + a zod schema instead.

* Migrated forms:
  * `pages/contacts/ContactListView.tsx` (inline create) — `contactCreateSchema`.
  * `pages/contacts/ContactDetailView.tsx` (edit) — `contactUpdateSchema`.
  * `pages/applications/ApplicationListView.tsx` (inline create) — `applicationCreateSchema`.
  * `pages/applications/ApplicationDetailView.tsx` (edit) — `applicationUpdateSchema`.
  * `pages/accomplishments/AccomplishmentListView.tsx` (inline create) — `accomplishmentCreateSchema`.
  * `pages/accomplishments/AccomplishmentDetailView.tsx` (edit) — `accomplishmentUpdateSchema`.
  * `pages/notes/NoteDetailView.tsx` (edit) — `noteUpdateSchema`.
  * `pages/resumes/ResumeDetailView.tsx` (rename / label) — `resumeUpdateSchema`.
  * `pages/resumes/{SummarySection,ContactSection,ExperienceSection,EducationSection,SkillsSection}.tsx` — sub-schemas under `resumeEntry.ts`.
  * `components/InlineCreateForm.tsx` — generic, accepts `schema` prop.
  * `components/CommunicationsPanel.tsx` — `communicationCreateSchema` / `communicationUpdateSchema`.
* Submit handlers no longer call `.trim()` manually; zod's transform handles it.
* `disabled` state on submit buttons driven by `formState.isSubmitting` (RHF) instead of local `loading` `useState`.
* Field-level errors render under each input via a small shared `<FieldError>` component reading `formState.errors[name]?.message`.

### R5 - Create/edit form parity for contacts, accomplishments, notes

Today, the create forms for contacts, accomplishments, and notes are bespoke list-page layouts (`newForm` / `formRow` / `formField` in `ContactListView`, `AccomplishmentListView`, `NoteListView`) while the corresponding edit forms in the detail views use a different, better-looking layout (`fieldRow` / `fieldGroup` grid). The edit forms are the canonical design; create must match.

* Extract one per-resource form component used by both list-page create and detail-page edit:
  * `pages/contacts/ContactForm.tsx` — consumed by `ContactListView` (create) and `ContactDetailView` (edit).
  * `pages/accomplishments/AccomplishmentForm.tsx` — same pattern.
  * `pages/notes/NoteForm.tsx` — same pattern.
* Each `<XForm>` accepts `{ mode: 'create' | 'edit'; defaultValues; onSubmit; onCancel }` and internally owns the `useForm()` + `zodResolver` wiring. `create` mode uses `xxxCreateSchema`; `edit` mode uses `xxxUpdateSchema`.
* Identical field set + visual layout across modes. Edit-only affordances (e.g., "Delete" buttons) live in the detail view *around* `<XForm>`, not inside it.
* CSS rule: forms reuse a single set of CSS module classes — `fieldRow` / `fieldGroup` / `fieldLabel` / `fieldInput` style names (R009 tokens). Delete the redundant `newForm` / `formRow` / `formField` / `formTitle` / `formError` blocks from `ContactListView.module.css`, `AccomplishmentListView.module.css`, `NoteListView.module.css`.
* List-page wrapper renders `<XForm mode="create" />` inside the same expand/collapse panel it does today; "Cancel" still hides the form, "Create" calls the mutation + closes.
* Detail-page edit toggle renders `<XForm mode="edit" defaultValues={detail} />` in place of the inline edit DOM that currently exists there.
* No layout regression in edit views — visual diff before/after for one contact, one accomplishment, one note detail page; expected diff zero.
* Field ordering and grouping comes from one place: the form component. List and detail pages do not re-declare it.

### R6 - Cleanup + no regressions

Old patterns gone; behavior parity preserved.

* All `useState<{...form fields}>` patterns in migrated files removed; verified by grep.
* All `setForm({...form, [name]: value})` change handlers removed (RHF `register()` replaces them).
* All `if (!form.x.trim())` validation guards removed (zod replaces them).
* `make check` (root) green: lint + typecheck + vitest + backend pytest.
* Manual smoke per migrated form: required-field error appears on submit + on blur, URL/email/date errors appear with correct copy, submit disables during in-flight, errors clear on edit.
* No new prop drilling: `useForm()` lives inside each form component, not lifted.

## Design

### Schema example (contact)

```ts
// frontend/src/schemas/contact.ts
import { z } from 'zod'

const trimmed = (max?: number) => {
  const s = z.string().trim()
  return max ? s.max(max) : s
}
const optionalTrimmed = (max?: number) =>
  trimmed(max).transform((v) => v || undefined).optional()

export const contactCreateSchema = z.object({
  name: trimmed(200).min(1, 'Name is required'),
  email: optionalTrimmed().pipe(z.string().email().optional()),
  phone: optionalTrimmed(50),
  role: optionalTrimmed(200),
  team_domain: optionalTrimmed(200),
  communication_preferences: optionalTrimmed(),
  interests: optionalTrimmed(),
  // ...
})
export type ContactCreateInput = z.infer<typeof contactCreateSchema>

export const contactUpdateSchema = contactCreateSchema.partial()
export type ContactUpdateInput = z.infer<typeof contactUpdateSchema>
```

### Form usage pattern (page-level)

```tsx
// pages/contacts/ContactListView.tsx (excerpt)
import { useForm, SubmitHandler } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { contactCreateSchema, type ContactCreateInput } from '../../schemas/contact'

function ContactCreateForm({ onCreated }: Props) {
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } =
    useForm<ContactCreateInput>({
      resolver: zodResolver(contactCreateSchema),
      mode: 'onBlur',
    })
  const { mutateAsync } = useContactMutations().create  // R008 hook

  const onSubmit: SubmitHandler<ContactCreateInput> = async (data) => {
    await mutateAsync(data)
    reset()
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <input {...register('name')} placeholder="Name" aria-invalid={!!errors.name} />
      <FieldError error={errors.name} />
      <input {...register('email')} placeholder="Email" aria-invalid={!!errors.email} />
      <FieldError error={errors.email} />
      <button type="submit" disabled={isSubmitting}>Add</button>
    </form>
  )
}
```

### EntryForm rebuild sketch

```tsx
// components/EntryForm.tsx (excerpt)
type Props<T extends FieldValues> = {
  fields: FieldConfig[]
  schema: z.ZodType<T>
  defaultValues: DefaultValues<T>
  onSubmit: SubmitHandler<T>
  onCancel: () => void
}

export function EntryForm<T extends FieldValues>({ fields, schema, defaultValues, onSubmit, onCancel }: Props<T>) {
  const form = useForm<T>({ resolver: zodResolver(schema), defaultValues, mode: 'onBlur' })
  const highlightsField = fields.find((f) => f.type === 'highlights')
  const highlightsArray = useFieldArray({
    control: form.control,
    name: (highlightsField?.name ?? 'highlights') as any,
  })
  // ...render fields by config, swap setState/validate for RHF register/handleSubmit
}
```

### `<FieldError>` shared component

```tsx
// components/FieldError.tsx
export function FieldError({ error }: { error?: FieldError }) {
  if (!error?.message) return null
  return <p role="alert" className={styles.fieldError}>{error.message}</p>
}
```

Single source of error rendering; uses R009 tokens for styling.

### Mapping backend Pydantic → zod

| Pydantic constraint | zod equivalent |
|---------------------|----------------|
| `Field(..., min_length=1, max_length=200)` | `z.string().trim().min(1).max(200)` |
| `EmailStr` | `z.string().email()` |
| `HttpUrl` | `z.string().url()` |
| `field_validator("date")` ISO date | `z.string().regex(/^\d{4}-\d{2}-\d{2}$/)` |
| `Optional[str]` empty → None | `z.string().trim().transform((v) => v \|\| undefined).optional()` |
| `Literal["a", "b"]` | `z.enum(['a', 'b'])` |

Document the table in `frontend/src/schemas/README.md` (single doc file — exception to the "no new markdown" rule because it's a load-bearing convention reference for future contributors).

### File layout

```
frontend/src/
  schemas/
    README.md                # new — Pydantic → zod mapping table
    contact.ts               # new
    application.ts           # new
    accomplishment.ts        # new
    note.ts                  # new
    resume.ts                # new
    resumeEntry.ts           # new — work/education/skill/summary/contactInfo
    communication.ts         # new
    index.ts                 # new — barrel
  components/
    EntryForm.tsx            # rebuilt
    InlineCreateForm.tsx     # rebuilt — generic, accepts schema
    FieldError.tsx           # new
    FieldError.module.css    # new
  __tests__/
    schemas/                 # new — one test file per schema
    components/
      EntryForm.test.tsx     # updated
      FieldError.test.tsx    # new
```

### Risks

* **Schema drift from Pydantic**: zod is hand-mirrored, not generated. Mitigation: contract tests at the API boundary already exist; the mapping table in `schemas/README.md` is the docs anchor. Generating zod from OpenAPI is out of scope (defer to a later plan if drift becomes a real problem).
* **`mode: 'onBlur'` UX**: required fields don't error until blur, which can feel sluggish for one-field inline forms. Use `mode: 'onChange'` for those; document the convention in `schemas/README.md`.
* **`useFieldArray` reorder behavior**: current `highlights` UI has no reorder — keep parity; do not add drag-reorder in this plan.
* **Form reset after R008 mutation success**: ensure `reset()` runs in `onSuccess` of the mutation (not after `await mutateAsync`) to handle race with cache invalidation cleanly.
* **`zodResolver` async**: schemas remain sync; if a future need (e.g., uniqueness check) requires async, wire `z.refine(async ...)` per-form only.

### Future work (out of scope)

* Generated zod schemas from FastAPI OpenAPI (`openapi-zod-client` or `orval`) — defer until drift hurts.
* Server-side validation error → form field mapping (e.g., parse 422 response into `setError`) — defer until backend returns structured field errors.
* Multi-step / wizard forms — none exist yet.

## Tasks

### P1 - Foundation

Add deps, build schemas, ship `<FieldError>`. No form refactor yet.

- [x] T01 Add `react-hook-form@^7`, `zod@^3`, `@hookform/resolvers@^3` to `frontend/package.json`; run install.
- [x] T02 Create `frontend/src/schemas/` with `contact.ts`, `application.ts`, `accomplishment.ts`, `note.ts`, `resume.ts`, `resumeEntry.ts`, `communication.ts`, `index.ts` per R2.
- [x] T03 Create `frontend/src/schemas/README.md` with the Pydantic → zod mapping table from Design.
- [x] T04 Create `components/FieldError.tsx` + `.module.css` (R009 tokens; status-error color).
- [x] T05 Add `__tests__/schemas/<resource>.test.ts` for each schema: happy path + each validation rule (≥3 cases per resource).
- [x] T06 Run `make check` (frontend) — schemas + tests green, no other code touched yet.

### P2 - Shared form components

Rebuild `EntryForm` + `InlineCreateForm` on RHF.

- [x] T07 Rebuild `components/EntryForm.tsx` per R3 (RHF + `useFieldArray` for highlights, `zodResolver`); accept `schema` + `defaultValues` props.
- [x] T08 Rebuild `components/InlineCreateForm.tsx` to accept generic `schema` prop and a single `register`-driven input layout.
- [x] T09 Update `__tests__/components/EntryForm.test.tsx` to assert zod error rendering + `useFieldArray` add/remove.
- [x] T10 Add `__tests__/components/FieldError.test.tsx`: renders message + `role="alert"`; renders nothing when no error.

### P3 - Per-resource shared form components

Extract one form component per resource and use it from both create and edit sites (R5). Land these before the rest of the migrations so the create/edit unification is a single reviewable change per resource.

- [x] T11 Create `pages/contacts/ContactForm.tsx` (RHF + `contactCreateSchema` / `contactUpdateSchema`, mode prop, full field set matching current edit layout); promote `fieldRow` / `fieldGroup` CSS from `ContactDetailView.module.css` to a shared module (e.g., `ContactForm.module.css`).
- [x] T12 Wire `<ContactForm mode="create" />` into `ContactListView` (replace `newForm` block); wire `<ContactForm mode="edit" defaultValues={contact} />` into `ContactDetailView` (replace inline edit DOM). Delete `newForm` / `formRow` / `formField` styles from `ContactListView.module.css`.
- [x] T13 Create `pages/accomplishments/AccomplishmentForm.tsx` (same pattern); migrate `AccomplishmentListView` + `AccomplishmentDetailView`; delete redundant list-page form styles.
- [x] T14 Create `pages/notes/NoteForm.tsx` (same pattern); migrate `NoteListView` + `NoteDetailView`; delete redundant list-page form styles.
- [ ] T15 Visual diff verification: screenshot each detail edit view before/after (3 resources) — expected zero diff. Screenshot each list create view before/after — expected to now match the edit layout.

### P4 - Remaining page migrations

One commit per resource area for clean review.

- [x] T16 Migrate `pages/applications/{ApplicationListView,ApplicationDetailView}.tsx` to RHF + application schemas (layouts diverge significantly; no shared ApplicationForm extracted per plan guidance).
- [x] T17 Migrate `pages/resumes/ResumeDetailView.tsx` (rename / label).
- [x] T18 Migrate `pages/resumes/{SummarySection,ContactSection}.tsx` (single-field forms — use `mode: 'onChange'`).
- [x] T19 Migrate `pages/resumes/{ExperienceSection,EducationSection,SkillsSection}.tsx` (EntryForm callers — pass the new `schema` prop).
- [x] T20 Migrate `components/CommunicationsPanel.tsx`.

### P5 - Cleanup + verification

- [x] T21 Grep `frontend/src` for residual `setForm\(`, `useState<.*[Ff]orm`, `\.trim\(\) ===`, `if \(![a-zA-Z]+\.trim\(\)\)` patterns; resolve holdouts.
- [x] T22 Grep for residual `styles.newForm` / `styles.formRow` / `styles.formField` / `styles.formTitle` / `styles.formError` references in `pages/{contacts,accomplishments,notes}/` — should be zero.
- [x] T23 Run `make check` (root) — lint + typecheck + vitest + backend pytest green.
- [ ] T24 Manual smoke per migrated form (R6): required errors on submit + blur, URL/email/date errors, submit disabled in-flight, errors clear on edit; for contacts/accomplishments/notes also verify create and edit views render identical field layout.
- [ ] T25 Measure prod bundle size before/after; record delta in PR description (target < +18 KB gzip).

### Implementation Notes

* **Sequence**: P1 → P2 → P3 → P4 → P5 strict. P3 (contacts/accomplishments/notes shared form extraction) is the user-visible win — land it cleanly before tackling P4. P3 + P4 commits parallelizable across an agent fleet (independent files), but serial review is cleaner.
* **Canonical layout is the edit view**: do not redesign in this plan. Copy the existing `fieldRow` / `fieldGroup` grid out of the detail view as-is into the shared `<XForm>`; promote its CSS module verbatim. Visual changes should be limited to the create flows now matching the edit flows.
* **Schemas come first**: every form migration depends on its schema. Land all schemas (P1) before any P3 task starts.
* **Coordination with R008 (TanStack Query)**: form `onSubmit` calls `mutation.mutateAsync(data)`; RHF awaits it, so `formState.isSubmitting` accurately reflects mutation in-flight. If R008 lands first this is free; if not, plain `fetch` works the same.
* **Coordination with R010 (Toast provider)**: replace any leftover inline status messages from form submits with `useToast()` calls in the migration — don't reintroduce them.
* **Don't over-fit `EntryForm`**: if a section's form has unique behavior, build a small bespoke form using RHF directly rather than bending `EntryForm` to fit. Three similar forms beats one over-generic abstraction.
* **`noValidate` on `<form>`**: needed so browser native validation doesn't fight zod (e.g., browser email validation rejecting blank-but-optional fields).
* **Type safety**: prefer `useForm<z.infer<typeof schema>>()` so field names autocomplete in `register()` calls.
