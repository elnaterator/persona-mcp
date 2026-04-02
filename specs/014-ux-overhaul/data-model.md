# Data Model: 014 UX Overhaul

## No Data Model Changes

This feature is **frontend-only**. No database schema changes, no new entities, no modifications to existing data models.

All existing entities (Resume, ResumeVersion, ContactInfo, WorkExperience, Education, Skill, Application, Accomplishment, Note) remain unchanged. The API contract between frontend and backend is unmodified.

## Frontend State Changes

The following component-level state changes are introduced (not persisted — ephemeral UI state):

### EditableSection State

```
Previous states: 'viewing' | 'editing' | 'saving'
New states:      'viewing' | 'hovering' | 'editing' | 'saving'

Transitions:
  viewing → hovering   (mouse enter / touch tap)
  hovering → viewing   (mouse leave / touch elsewhere)
  hovering → editing   (click edit icon / second tap)
  editing → saving     (click save)
  editing → viewing    (click cancel / Escape / navigate away)
  saving → viewing     (save success)
  saving → editing     (save error)
```

### InlineCreateForm State

```
States: 'collapsed' | 'open' | 'submitting'

Transitions:
  collapsed → open        (click "Add Version" button)
  open → collapsed        (click cancel / Escape)
  open → submitting       (submit with valid input)
  submitting → collapsed  (success — form closes, list refreshes)
  submitting → open       (error — form stays open with error message)
```

### Navigation — Connect Tab Highlighting

No new state. The existing React Router `NavLink` `isActive` detection continues to work. The visual differentiation of the Connect tab is purely CSS-based (additional class for the Connect NavLink).
