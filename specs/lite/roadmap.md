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


## Refactor user interface to organize and reuse components

Should have a `pages/` dir, separate subdir for each page with page and components specific to page.  Top level `components/` dir for shared/reusable components across pages. Improve reuse of components. Rename frontend/src/types/resume.ts, it has all types. Update AGENTS.md to explain frontend org. Suggest other high value front end refactors.


## Remove application contacts and communications, use links instead

Remove duplicate functionality from applications, use linked contacts and contact communications. Just have list of linked resources like all other pages. No need to preserve existing application contacts or communications, just delete (early in project, no users yet).


