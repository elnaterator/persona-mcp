# Roadmap

These are upcoming epics to implement.

---

## UI Look and Feel Tweaks

Status: In Progress

I want to make the UX better
* I want the home page on login to be the connect tab, it should stand out from the rest
* I want the menu bar on top to look better with some icons, a nicer color scheme
* I want a dark theme for the website with a clean, simple design, minimalist, not all rounded, more with simple lines, it should remind you of a terminal, software engineering, some green blinking cursor, monospace font, but cool and modern at the same time
* When adding a new resume version, don't use an alert pop up, make it a better UX than that
* The resume should look more like a resume, while still being functional to add/edit integrated into the UI on hover over elements, but when not hovering it should look similar to a resume

---

## Separate endpoints for Jobs vs Notes vs Both

Status: Not Started

I should have 3 separate URLs that I can configure when connecting to the MCP server:
* One only exposes the Notes functionality
* One only exposes the Jobs functionality
* One exposes all functionality

---

## Deploy to Production Properly

Status: Not Started

We should deploy persona to productin at persona.nathanhadzariga.com and have it use the production instance of the Neon DB and the production Clerk authentication.

---

## Add evals to the MCP server

Status: Not Started

I want to add evals to test the MCP server using Promptfoo.  It should start simple with only high value evals that run fairly quickly, I will incrementally enhance later once I am comfortable with evals. 

---

## Live Resume Preview with Print/PDF Export

Status: Not Started

**Problem:** The resume editor is entirely form-based — users fill in fields across five sections (contact, summary, experience, education, skills) but never see what their resume actually looks like. For a resume tool, this is the single biggest gap. Users must mentally assemble the final output, with no visual feedback loop as they edit.

**Proposed change:**
- Add a side-by-side layout: editor panel on the left, live-rendered resume preview on the right.
- The preview updates in real-time as users type, showing a properly typeset document (name/contact header, summary paragraph, experience with bullet points, education, skills grid).
- Include a "Print / Export PDF" button that uses `window.print()` with a dedicated print stylesheet (the app already has basic `@media print` rules in `index.css` — expand these into a full resume layout).
- On mobile, the preview becomes a toggle (edit view vs. preview view) rather than side-by-side.

**Why highest impact:** A resume tool that doesn't show the resume is like a word processor without a page. This single change transforms the app from "a database with forms" into "a resume builder." Users get immediate visual feedback, can iterate on wording while seeing the result, and can export a professional document without leaving the app.

---

## Kanban Board for Application Pipeline

Status: Not Started

**Problem:** The application tracker displays jobs as a flat, filterable list. Job seekers typically manage 10–50+ applications simultaneously across stages (Interested → Applied → Phone Screen → Interview → Offer/Rejected). The current list view makes it hard to see the pipeline at a glance — users must mentally group applications by status and click through filters to focus on a specific stage.

**Proposed change:**
- Replace (or supplement) the list view with a kanban-style board where each column represents an application status.
- Cards show company name, position, and last-updated date. Color-coding already exists for status badges — apply it to column headers.
- Drag-and-drop cards between columns to update status (fires a PATCH to `/api/applications/{id}`).
- Keep the existing list view as an alternative (toggle between "Board" and "List" views) for users who prefer it or are on mobile.
- Each column shows a count badge so users can see their pipeline distribution instantly (e.g., "12 Applied, 3 Interviewing, 1 Offer").

**Why highest impact:** Pipeline visibility is the core job of an application tracker. A kanban board gives users a spatial mental model of their job search — they can see where they're heavy, where things are stalling, and what needs attention. Drag-and-drop status changes also eliminate the current flow of: open application → change dropdown → save → go back to list.

---