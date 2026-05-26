# Roadmap


## R000 Update home page with latest info - DONE

Home page "Your career data, organized." shows on 2 lines, make it 1.  Show resumes, applications, accomplishments, missing notes and contacts.


## R001 Common pool of tags across all resource types - DONE

Rather then separate tags for accomplishments and notes, make it common across all types. Tags added on a note should be recommended when adding a tag to accomplishment and vice versa.  Also add tags to resumes and applications. 


## R002 Add contacts feature - DONE

I want a new section for "Contacts". Should have another page for contacts, allow CRUD operations on contacts, include updates to REST API, MCP tools, and UI.  Should include typical contact information as well as fields to help with work relationships and networking during job search.  Possible examples: communication preferences, interests, role, team/domain, what they care about, current priorities, collaboration opportunities, etc.  Suggest any fields that make sense for work or career related contacts without making it overly complicated, help me with this design. Think carefully about best data model.  Contacts should be taggable as well. 


## R003 Keep communication history for each contact - DONE

CRUD operations for comms on contacts, and in the UI see and manage (add/edit/delete) communications. Should appear in communication section below contact details.  Support tags on communications.  Need feature to search all communication across contacts (by tag or text search), dedicated page not needed, can be feature integrated into the contacts page.


## R004 Link notes to any other resource - DONE

Should use many to many relationship. Notes may be associated to applications, accomplishments, resumes, and contacts.  On the notes page should have boxes with count for each type (3 linked accomplishments, 2 linked contacts).  Click to show list of linked items, click to go to linked item. On other pages should have similar, with linked notes count, if any, click to show list, click on list item to go to note. On notes list page, should show num linked items.


## R005 Link contacts to any other resource - DONE

Should use many to many relationship. Contacts may be associated to applications, accomplishments, resumes, and notes.  On the contacts page should have boxes with count for each type (3 linked accomplishments, 2 linked resumes).  Click to show list of linked items, click to go to linked item. On other pages should have similar, with linked contacts count, if any, click to show list, click on list item to go to contact.  On contacts list page, should show num linked items.  Note that this should align with the same linking approach as used for notes.


## R006 Refactor user interface to organize and reuse components - DONE

Should have a `pages/` dir, separate subdir for each page with page and components specific to page.  Top level `components/` dir for shared/reusable components across pages. Improve reuse of components. Rename frontend/src/types/resume.ts, it has all types. Update AGENTS.md to explain frontend org. Suggest other high value front end refactors.


## R007 Remove application contacts and communications, use links instead - DONE

Remove duplicate functionality from applications, use linked contacts and contact communications. Just have list of linked resources like all other pages. No need to preserve existing application contacts or communications, just delete (early in project, no users yet).


## R008 Adopt TanStack Query for server state - DONE

Replace per-view `useEffect(fetch, [])` + manual `refresh()` pattern with `useQuery` / `useMutation`. Cache list + detail responses, dedup in-flight requests, refetch on focus, invalidate on mutate. Enables instant back-nav, optimistic updates for tag/link toggles. Replaces or thins out `useResourceList` / `useResourceDetail` hooks.


## R009 Theme tokens (CSS variables) - DONE

Define `:root` CSS vars in `index.css` for spacing, colors, radii, shadows (`--space-1..8`, `--color-fg/bg/accent`, `--radius-sm/md`, `--shadow-card`). Sweep all `*.module.css` to reference vars instead of hardcoded hex/px. Enables dark mode + design-system consistency. Low risk, high visual payoff.


## R010 Toast / notification provider - DONE

Replace per-view `StatusMessage` state + auto-dismiss timers with single `<ToastProvider>` at root + `useToast()` hook. Single render slot, queue, animation, no prop drilling. Cuts ~10 LOC per list/detail view.


## R011 Form abstraction (react-hook-form + zod) - DONE

Replace hand-rolled field state + validation in `EntryForm`, `ContactDetailView`, `ApplicationDetailView` with `react-hook-form` (uncontrolled, fast) + `zod` schemas (single source of truth, infer TS types). Kills validation drift between client + server.


## R012 Storybook and playwright for shared components and e2e UI tests - DEFERRED

Set up Storybook targeting `frontend/src/components/`. Stories per primitive (`Breadcrumb`, `ConfirmDialog`, `EditableSection`, `LinkPickerModal`, `TagInput`, `LinksPanel`, etc.) with props matrix + a11y addon. Enables isolated visual review and future visual-regression testing (Chromatic). Defer until shared component set stabilizes. I want to set up a playwright test suite to validate the behavior of the running UI as well as validation of look and feel. It should not be part of the CI pipeline yet.

**Deferred (2026-05-23):** Too early. The shared component set is still churning — R015 (compact lists) and R016 (reusable search component) will reshape the exact primitives Storybook would document, so stories + visual baselines would rot immediately. Playwright e2e has standalone value, but keeping it out of CI on a solo project means it won't run and will rot. Revisit after R014/R015/R016 settle the UI; then add a thin CI-gated Playwright smoke suite first, and Storybook only if a real shared-primitive library or collaborators emerge. Plan drafted at `specs/lite/012-storybook-playwright-plan.md` (on hold).


## R013 Remove application to resume duplicate linking mechanism, use generic links - DONE

`application.resume_version_id` FK duplicates the generic `link` table edge `application↔resume`. Drop the column and the matching `Application.resume_version_id` / `ApplicationSummary.resume_version_id` model fields, the `resume_version_id` param on `application_tools.py` create/update, and the resume-picker UI in `ApplicationDetailView` (replace with the standard `LinksPanel` resume entries). Replace `ResumeVersion.app_count` (currently a JOIN aggregate over the FK) with the existing generic `link_count` filtered to `type=application`, and update the resume list-card "X applications" badge accordingly. Migration must backfill existing `resume_version_id` values into `link` rows before dropping the column. No "primary resume per application" semantics preserved — generic links allow many resumes per app with no primary; revisit with a `primary_resume_link_id` flag only if the UX requires it.


## R014 Render lists in more compact form - DONE

Resume list items look good, make other list items similar, more compact, fit all on one line where possible, 2 if not, float right for things like dates, link counts, etc. The goal is clean, good looking, and compact to show more items at once.


## R015 Consistent search experience - DONE

Create a single search bar as a reusable component that is consistent across the application. Both tags and text in a single search bar. As you type it should recommend tags, use tab to complete the tag, or click on item from recommendations list.  When tag added, add as a chip in search bar, float left.  Any typed text that is not part a tag is used as search text. For all object types we can search by tags or text, consistent experience. There should also be a generic search API across all resources, and a search bar on the home page tha returns results for any resource.

## R016 Use standard OAuth2 flow for MCP server auth, rather than API keys

Shouldn’t have to configure API keys to connect to MCP server, should use OAuth2 flow. The MCP command should just point at URL, Unauthenticated request returns WWW-Authenticate header with Protected Resource Metadata at `/.well-known/oauth-protected-resource/mcp`, use clerk as OAuth2 provider.  Ask good questions to guide any good design.  Include tasks in plan for manual setup steps in clerk (clearly indicate these are human, manual steps). Clean up API key handling on home page.