# Roadmap


## Update home page with latest info - DONE

Home page "Your career data, organized." shows on 2 lines, make it 1.  Show resumes, applications, accomplishments, missing notes and contacts.


## Common pool of tags across all resource types - DONE

Rather then separate tags for accomplishments and notes, make it common across all types. Tags added on a note should be recommended when adding a tag to accomplishment and vice versa.  Also add tags to resumes and applications. 


## Add contacts feature - DONE

I want a new section for "Contacts". Should have another page for contacts, allow CRUD operations on contacts, include updates to REST API, MCP tools, and UI.  Should include typical contact information as well as fields to help with work relationships and networking during job search.  Possible examples: communication preferences, interests, role, team/domain, what they care about, current priorities, collaboration opportunities, etc.  Suggest any fields that make sense for work or career related contacts without making it overly complicated, help me with this design. Think carefully about best data model.  Contacts should be taggable as well. 


## Keep communication history for each contact - DONE

CRUD operations for comms on contacts, and in the UI see and manage (add/edit/delete) communications. Should appear in communication section below contact details.  Support tags on communications.  Need feature to search all communication across contacts (by tag or text search), dedicated page not needed, can be feature integrated into the contacts page.


## Link notes to any other resource - DONE

Should use many to many relationship. Notes may be associated to applications, accomplishments, resumes, and contacts.  On the notes page should have boxes with count for each type (3 linked accomplishments, 2 linked contacts).  Click to show list of linked items, click to go to linked item. On other pages should have similar, with linked notes count, if any, click to show list, click on list item to go to note. On notes list page, should show num linked items.


## Link contacts to any other resource - DONE

Should use many to many relationship. Contacts may be associated to applications, accomplishments, resumes, and notes.  On the contacts page should have boxes with count for each type (3 linked accomplishments, 2 linked resumes).  Click to show list of linked items, click to go to linked item. On other pages should have similar, with linked contacts count, if any, click to show list, click on list item to go to contact.  On contacts list page, should show num linked items.  Note that this should align with the same linking approach as used for notes.


## Refactor user interface to organize and reuse components - DONE

Should have a `pages/` dir, separate subdir for each page with page and components specific to page.  Top level `components/` dir for shared/reusable components across pages. Improve reuse of components. Rename frontend/src/types/resume.ts, it has all types. Update AGENTS.md to explain frontend org. Suggest other high value front end refactors.


## R007 Remove application contacts and communications, use links instead - DONE

Remove duplicate functionality from applications, use linked contacts and contact communications. Just have list of linked resources like all other pages. No need to preserve existing application contacts or communications, just delete (early in project, no users yet).


## R008 Adopt TanStack Query for server state

Replace per-view `useEffect(fetch, [])` + manual `refresh()` pattern with `useQuery` / `useMutation`. Cache list + detail responses, dedup in-flight requests, refetch on focus, invalidate on mutate. Enables instant back-nav, optimistic updates for tag/link toggles. Replaces or thins out `useResourceList` / `useResourceDetail` hooks.


## R009 Theme tokens (CSS variables)

Define `:root` CSS vars in `index.css` for spacing, colors, radii, shadows (`--space-1..8`, `--color-fg/bg/accent`, `--radius-sm/md`, `--shadow-card`). Sweep all `*.module.css` to reference vars instead of hardcoded hex/px. Enables dark mode + design-system consistency. Low risk, high visual payoff.


## R010 Toast / notification provider

Replace per-view `StatusMessage` state + auto-dismiss timers with single `<ToastProvider>` at root + `useToast()` hook. Single render slot, queue, animation, no prop drilling. Cuts ~10 LOC per list/detail view.


## R011 Form abstraction (react-hook-form + zod)

Replace hand-rolled field state + validation in `EntryForm`, `ContactDetailView`, `ApplicationDetailView` with `react-hook-form` (uncontrolled, fast) + `zod` schemas (single source of truth, infer TS types). Kills validation drift between client + server.


## R012 Storybook for shared components

Set up Storybook targeting `frontend/src/components/` (post-refactor). Stories per primitive (`Breadcrumb`, `ConfirmDialog`, `EditableSection`, `LinkPickerModal`, `TagInput`, `LinksPanel`, etc.) with props matrix + a11y addon. Enables isolated visual review and future visual-regression testing (Chromatic). Defer until shared component set stabilizes.


## R013 UI test suite with playwright

I want to set up a playwright test suite to validate the behavior of the running UI as well as validation of look and feel. It should not be part of the CI pipeline yet.
