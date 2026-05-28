# Prompts for fast lite work

Copy/paste one block per step. `NNN` = roadmap item number (R015 → `015`). Each feature runs in its own git worktree, so multiple features run in parallel with no file or seq-num collisions.


## Work Sequentially from Main Branch

### Design and Plan

You are staff software engineer, value clean code, high quality UI/UX. Read roadmap item not marked DONE from specs/lite/roadmap.md. Create plan in specs/lite/<seq_num>-<description>-plan.md. Use template specs/lite/plan-template.md. Use caveman skill, ultra. Roadmap item: 

### Implement

You are staff software engineer, value clean code, high quality UI/UX, if refactor recommended, do if small, ask if big. Use TDD if possible. Never deploy code or apply infra changes, local only. Ask if clarification needed. Read plan specs/lite/<seq_num>-*.md and implement all tasks, mark tasks complete as you go in plan. When done run `make check`, if passes mark corresponding roadmap item as done in specs/lite/roadmap.md. Plan: 

### Commit and PR

Check if curr branch name good, create new branch if needed, never commit to main. Use caveman-commit skill. Commit all changes, including specs/lite/*.md except plans with higher seq nums. Ask for confirm, then push to remote and use github mcp to create PR, curr branch -> main, PR description sections: motivation, what changed, testing (with checkboxes). Plan seq num: 


## Work in Parallel via Worktree

## Design and Plan

You are staff software engineer, value clean code, high quality UI/UX. For the roadmap item below, pick `NNN` = its number and a short kebab `slug` from its title. Create an isolated worktree as a SIBLING of this repo (never nested inside it) so this feature runs in parallel. Compute the absolute sibling path from the repo root, do not rely on bare `../`: `WT="$(git rev-parse --show-toplevel)/../persona-NNN"; git worktree add "$WT" -b feat/NNN-slug main`. Then verify with `git worktree list` that the new worktree path is a sibling of the repo (NOT a subdir of it) before continuing. Read `specs/lite/roadmap.md` for context. Write the plan to the worktree using its absolute path — `"$WT/specs/lite/NNN-slug-plan.md"` (do NOT write to a guessed/relative path) — using template `specs/lite/plan-template.md`. Use caveman skill, ultra. When done, print the `cd "$WT"` command so I can run Implement there. Roadmap item:

## Implement

You are staff software engineer, value clean code, high quality UI/UX, if refactor recommended, do if small, ask if big. Run from the feature worktree (the sibling dir created by Design — `cd` into the absolute path it printed, e.g. `cd "$(git rev-parse --show-toplevel)/../persona-NNN"`; confirm `git rev-parse --show-toplevel` ends in `/persona-NNN` before proceeding). Use TDD if possible. Never deploy code or apply infra changes, local only. Ask if clarification needed. Read plan `specs/lite/NNN-*-plan.md` and implement all tasks, mark tasks complete as you go in plan. When done run `make check`; if it passes, mark the matching roadmap item DONE in `specs/lite/roadmap.md`. (`make check` is parallel-safe. If you start a dev server / `make run` for manual UI testing, only one worktree can hold the default ports at a time.) Plan NNN:


## Commit and PR

Run from the feature worktree; you are already on branch `feat/NNN-slug` (never commit to main). Use caveman-commit skill. Stage and commit only: code changes, `specs/lite/NNN-*-plan.md`, `specs/lite/roadmap.md`. Ask for confirm, then push to remote and use github mcp to create PR, curr branch -> main, PR description sections: motivation, what changed, testing (with checkboxes). After the PR merges, clean up from the main repo (the `[main]` checkout, not this worktree): copy the worktree's absolute path from `git worktree list`, then `git worktree remove <that-abs-path>`. Plan NNN:
