# Feature Specification: UX Overhaul — Terminal-Inspired Dark Theme & Interface Improvements

**Feature Branch**: `014-ux-overhaul`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "UX Overhaul: terminal-inspired dark theme, connect tab as home, improved navigation, resume view, and better modal interactions"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Terminal-Inspired Dark Theme Applied Site-Wide (Priority: P1)

A user opens the application and is immediately presented with a cohesive dark theme. The visual design evokes a terminal / software engineering aesthetic: dark backgrounds, minimal decoration, crisp lines (not rounded), monospace typography, and a signature green blinking cursor accent. The experience feels modern and intentional — not just a generic dark mode.

**Why this priority**: The dark theme is the foundational visual layer that all other UX improvements build upon. It must ship first because every other story's acceptance depends on it.

**Independent Test**: Open the app in a browser. Verify the page renders with a dark background, monospace font, green accent color, and no rounded card/button shapes. Delivers a fully usable (if unpolished) application with the new aesthetic.

**Acceptance Scenarios**:

1. **Given** the application is opened, **When** the page loads, **Then** all backgrounds use a near-black or very dark color, all primary text is light-colored, and no bright white areas are visible.
2. **Given** any page is viewed, **When** inspecting typography, **Then** body and UI text uses a monospace typeface throughout.
3. **Given** any interactive element (button, input, tab) is present, **When** viewed, **Then** it has squared/sharp corners rather than rounded corners, using straight lines as dividers.
4. **Given** the interface, **When** a green blinking cursor accent is visible (e.g., in the header or hero area), **Then** it blinks at a natural cadence (roughly 1 second on/off) in a terminal green color.
5. **Given** any page is displayed, **When** the user has not set any explicit preference, **Then** the dark theme is the default and only theme.

---

### User Story 2 - Connect Tab as the Default Landing Page (Priority: P2)

After logging in, the user is taken directly to the Connect tab — not the Resume or any other section. The Connect tab is visually distinct from other tabs to signal it is the primary entry point and the most important section.

**Why this priority**: Establishes the correct navigational hierarchy and sets user expectations immediately on login. Directly impacts first impressions.

**Independent Test**: Log in. Verify the Connect tab is active and its content is displayed. Verify the Connect tab has a visually distinct treatment (color, weight, or indicator) compared to other tabs. Delivers clear navigational intent.

**Acceptance Scenarios**:

1. **Given** a user successfully authenticates, **When** they are redirected to the application, **Then** the Connect tab is the active/selected tab and its content panel is displayed.
2. **Given** the navigation bar is visible, **When** viewing any tab, **Then** the Connect tab has a visually differentiated style (e.g., highlighted, accented, or bold) compared to Resume, Notes, and other tabs.
3. **Given** a user manually navigates away and returns to the root URL, **When** the page loads, **Then** the Connect tab is selected by default.

---

### User Story 3 - Connect Page Decluttered and Visually Appealing (Priority: P3)

The Connect tab content is redesigned to feel like a polished landing page, not a dense form or data dump. Because it is the first thing users see after login, it must make a strong first impression: generous whitespace, clear visual hierarchy, a focused primary action or message, and only the most essential information visible at a glance. Secondary details are accessible but not overwhelming.

**Why this priority**: As the default landing page, the Connect tab is the highest-visibility surface in the product. Clutter here undermines the entire experience before the user has done anything.

**Independent Test**: Log in and land on the Connect tab. Ask a first-time viewer to describe what the page is for within 5 seconds. Verify they can identify the primary action or purpose without scrolling or reading every element. Delivers a first impression that matches the product's quality bar.

**Acceptance Scenarios**:

1. **Given** the Connect tab is displayed, **When** viewed at a glance, **Then** the primary purpose or action of the page is immediately clear without scrolling.
2. **Given** the Connect tab is displayed, **When** compared to the previous design, **Then** the number of simultaneously visible UI elements is reduced — secondary content is grouped, collapsed, or de-emphasized.
3. **Given** the Connect tab is displayed, **When** the layout is observed, **Then** there is clear visual hierarchy: a prominent heading or identity element, a defined primary action area, and supporting content that does not compete for attention.
4. **Given** the Connect tab is displayed using the dark theme, **When** viewed, **Then** spacing and layout create a sense of breathing room rather than density.
5. **Given** the Connect tab contains any generated output (e.g., a shareable link or profile summary), **When** displayed, **Then** that output is presented as the focal point of the page rather than buried among controls.

---

### User Story 4 - Improved Navigation Bar with Icons (Priority: P4)

The top navigation bar is redesigned with icons alongside tab labels, a refined color palette that fits the dark theme, and clear active/hover states. The bar reads as purpose-built for this product rather than a generic nav strip.

**Why this priority**: Improves navigational clarity and reinforces visual identity. Depends on the dark theme (P1) being in place.

**Independent Test**: View the navigation bar. Confirm each tab has an icon, the active tab is clearly highlighted, and hover states are visible. No functional regressions to navigation.

**Acceptance Scenarios**:

1. **Given** the navigation bar is displayed, **When** viewing each tab item, **Then** a relevant icon is shown to the left of or above the tab label.
2. **Given** the navigation bar is displayed, **When** a tab is active, **Then** the active tab is visually distinguished (e.g., accent color underline, highlighted background, or bolded label) from inactive tabs.
3. **Given** the navigation bar is displayed, **When** hovering over an inactive tab, **Then** a hover state is shown that gives clear affordance for clickability.
4. **Given** the navigation bar is displayed on narrow viewports, **When** the window is resized, **Then** the navigation remains usable (icons may collapse labels if needed).

---

### User Story 5 - Resume Section Looks Like a Real Resume (Priority: P5)

When viewing the Resume section without hovering, the content is displayed in a clean, resume-like layout: structured sections, appropriate hierarchy, readable typography — resembling a traditional resume document. When the user hovers over a section or field, subtle inline edit controls appear, allowing them to edit content in-place. The editing experience is integrated directly into the resume layout, not in a separate form or dialog.

**Why this priority**: Improves the perceived quality of the tool's primary content area. Depends on the dark theme (P1) and doesn't affect the connect or navigation stories.

**Independent Test**: Open the Resume tab. Verify the layout resembles a resume at rest. Hover over a field. Verify edit controls appear inline. Edit and save. Verify the resume view is restored. Delivers a fully functional resume management experience with improved presentation.

**Acceptance Scenarios**:

1. **Given** the Resume tab is open, **When** no element is being hovered, **Then** the page displays content in a structured resume format with clear section headings, name/contact prominently at the top, and no visible edit buttons or form inputs.
2. **Given** the Resume tab is open, **When** the user hovers over an editable section or field, **Then** inline edit affordances appear (e.g., an edit icon, underline, or subtle highlight) without disrupting the layout.
3. **Given** an inline edit affordance is visible, **When** the user clicks to edit, **Then** the field transitions to an editable input in-place without a full-page redirect or overlay dialog.
4. **Given** an inline edit is in progress, **When** the user confirms the change, **Then** the field returns to its resume-like read state with the updated value.
5. **Given** an inline edit is in progress, **When** the user cancels or presses Escape, **Then** the field returns to its original read state with no change.
6. **Given** an inline edit is in progress with unsaved changes, **When** the user navigates to another tab, **Then** the unsaved changes are discarded silently and the field reverts to its previous value.

---

### User Story 6 - Add New Resume Version Without an Alert Dialog (Priority: P6)

When a user creates a new resume version, the interaction is handled through an inline panel, slide-in drawer, or modal styled to match the dark theme — not a browser-native `alert()` or `confirm()` popup. The new version entry form is clearly identifiable and dismissible.

**Why this priority**: Removes the most jarring UX anti-pattern in the current experience. Relatively self-contained change.

**Independent Test**: Trigger the "add resume version" action. Verify no native browser alert/confirm dialog fires. Verify a styled UI component collects the version name/details. Complete the flow and verify the new version appears in the list.

**Acceptance Scenarios**:

1. **Given** the user clicks the "Add Version" control, **When** the action fires, **Then** no native browser `alert`, `confirm`, or `prompt` dialog appears.
2. **Given** the add-version action is triggered, **When** the styled input component appears, **Then** it is visually consistent with the dark theme and allows the user to enter version details.
3. **Given** version details are entered, **When** the user confirms, **Then** the new version is created and appears in the version list without a page reload.
4. **Given** the add-version component is open, **When** the user dismisses it (cancel button or Escape key), **Then** the component closes with no version created.

---

### Edge Cases

- When a user's resume has no content, the resume-like layout displays labeled section placeholders (e.g., "Work Experience", "Education") with "Click to add" prompts in each, preserving the resume structure and teaching the layout.
- On touch/mobile devices, a single tap on a resume section reveals edit controls; a second tap activates editing. This keeps the read-only resume clean on mobile by default.
- If the user navigates away mid-inline-edit, unsaved changes are discarded silently and the field reverts to its previous value. No confirmation prompt is shown.
- If the "add resume version" form is submitted with an empty or duplicate version name, inline validation errors are displayed within the styled component — no native alerts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST render with a dark color scheme as the default and only visual theme — no light mode toggle is required.
- **FR-002**: All text throughout the application MUST use a monospace typeface.
- **FR-003**: Interactive elements (buttons, tabs, inputs) MUST use sharp/straight corners with no rounded borders.
- **FR-004**: The interface MUST include a green blinking cursor accent visible in at least one prominent location (e.g., navigation header or page title area).
- **FR-005**: Upon successful login, the application MUST route users to the Connect tab as the default landing view.
- **FR-006**: The Connect tab MUST be visually differentiated from other navigation tabs to signal its primary importance.
- **FR-007**: Each navigation tab MUST display an icon alongside its text label.
- **FR-008**: The navigation bar MUST provide visible active and hover states for all tab items.
- **FR-009**: The Resume section MUST display content in a structured, resume-like read view when no element is being interacted with.
- **FR-010**: Resume section fields MUST reveal inline edit controls on hover, allowing in-place editing without navigating away or opening a separate page.
- **FR-011**: Inline edit interactions MUST support confirmation (save) and cancellation (discard), returning to the read-only resume view after either action.
- **FR-012**: The "add new resume version" action MUST NOT use a native browser `alert`, `confirm`, or `prompt` dialog.
- **FR-013**: Adding a new resume version MUST be handled by an application-native UI component (inline form, drawer, or styled modal) consistent with the dark theme.
- **FR-014**: The add-version component MUST be dismissible without creating a version (via cancel control or Escape key).
- **FR-015**: The resume read view MUST hide all edit UI (buttons, form inputs) when the user is not hovering over an editable area.
- **FR-016**: The Connect tab content MUST be organized with clear visual hierarchy — a primary focal element, a primary action, and de-emphasized secondary content.
- **FR-017**: The Connect tab MUST NOT display all available controls and information at equal visual weight — secondary or rarely-needed elements MUST be visually subordinate or hidden by default.
- **FR-018**: The Connect tab layout MUST use generous whitespace so content does not appear dense or cluttered.
- **FR-019**: When a resume has no content, the resume view MUST display labeled section placeholders with "Click to add" prompts, preserving the resume structure.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of pages and components render using the dark theme — zero white or light-background areas visible under normal use.
- **SC-002**: The Connect tab is displayed as the active view for 100% of post-login landing sessions.
- **SC-003**: Users can initiate, complete, and cancel inline resume edits without leaving the resume view in 100% of attempts.
- **SC-004**: Zero native browser dialogs (`alert`/`confirm`/`prompt`) appear during any resume version creation flow.
- **SC-005**: All navigation tab items display an icon in 100% of viewport sizes where the nav is visible.
- **SC-006**: A first-time observer can identify which tab is active without any additional context — active state passes a visual clarity check (distinguishable at a glance).
- **SC-007**: A resume with populated data is recognizable as a resume document at first glance in the read-only state — no edit controls visible until hover.
- **SC-008**: A first-time viewer can state the primary purpose of the Connect tab within 5 seconds of landing on it, without scrolling.
- **SC-009**: The Connect tab displays no more than one primary action as the dominant interactive element — all other controls are visually secondary.

## Clarifications

### Session 2026-03-27

- Q: How should inline edit controls work on touch/mobile devices where hover is unavailable? → A: A single tap on a section reveals edit controls; a second tap activates editing.
- Q: What happens when a user navigates away during an inline edit with unsaved changes? → A: Discard unsaved changes silently — the field reverts to its previous value.
- Q: How should the resume layout handle an empty/new resume with no content? → A: Show the resume structure with labeled section placeholders and "Click to add" prompts in each section.

## Assumptions

- The current application has a tabbed navigation structure with at minimum: Connect, Resume, and Notes tabs.
- The existing resume section contains fields and sections that map to standard resume content (work experience, education, skills, etc.).
- "Connect tab" refers to the tab where users share or generate their professional connection/contact profile, not a network connectivity page.
- On touch/mobile devices, inline editing uses a two-tap interaction: first tap reveals edit controls, second tap activates editing — keeping the resume read view clean by default.
- A single global dark theme is sufficient; per-user theme preference storage is out of scope for this feature.
- The green blinking cursor is a decorative accent only and does not require any functional behavior (no text input cursor behavior needed).
- The add-version UI component (drawer/modal/inline form) style is left to implementation discretion as long as it is consistent with the dark theme and avoids native dialogs.

## Dependencies

- Existing tabbed navigation component (to be restyled and extended with icons)
- Existing resume data model and edit forms (to be reorganized into inline-edit resume view)
- Existing resume version creation flow (to replace native dialog with styled component)
- Clerk authentication redirect configuration (to enforce Connect tab as post-login destination)
