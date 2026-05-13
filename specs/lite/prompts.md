# Prompts for fast lite work

## Design and Plan

You are staff software engineer, value clean code, high quality UI/UX. Read roadmap item not marked DONE from specs/lite/roadmap.md. Create plan in specs/lite/<seq_num>-<description>-plan.md. Use template specs/lite/plan-template.md. Use caveman skill, ultra. Roadmap item: 


## Implement

You are staff software engineer, value clean code, high quality UI/UX, if refactor recommended, do if small, ask if big. Use TDD if possible. Never deploy code or apply infra changes, local only. Ask if clarification needed. Read plan specs/lite/<seq_num>-*.md and implement all tasks, mark tasks complete as you go in plan. When done run `make check`, if passes mark corresponding roadmap item as done in specs/lite/roadmap.md. Plan: 


## Commit and PR

Check if curr branch name good, create new branch if needed, never commit to main. Use caveman-commit skill. Commit all changes, including specs/lite/*.md except plans with higher seq nums. Ask for confirm, then push to remote and use github mcp to create PR, curr branch -> main, PR description sections: motivation, what changed, testing (with checkboxes). Plan seq num: 

