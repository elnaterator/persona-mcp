# Plan 019 - Rename the app to pktx and clean up docs

Date: 2026-07-10

Rename the app from **persona** to **pktx** (short for "personal context") across code, config,
infra, and docs. Clean up README/docs, organize the repo for open source (LICENSE,
CONTRIBUTING.md), and write a manual-steps checklist for everything that cannot be renamed
from inside the repo (GitHub, Neon, Clerk, AWS, local dev machines).

Branch: `chore/019-rename-pktx`


## Requirements

### R1 - Code identity renamed to pktx

All in-repo identifiers move from `persona` to `pktx`. Clean cut — no backward-compat
aliases for env vars or the CLI entry point (pre-beta, single deployment, acceptable).

* Python package dir is `backend/src/pktx`; all imports use `pktx.*`.
* `pyproject.toml`: project name `pktx`, script entry `pktx = "pktx.server:main"`, packages `["src/pktx"]`.
* All `PERSONA_*` env vars renamed to `PKTX_*` (PUBLIC_URL, FRONTEND_DIR, DB_URL, PORT, USER_ID, DB_POOL_MIN/MAX, CORS_ORIGINS, DATA_DIR) in code, tests, `.env.example`, compose, Dockerfile, infra, docs.
* `docker-compose.yml`: service, POSTGRES_USER/PASSWORD/DB, healthcheck, and DB URL use `pktx`.
* Frontend branding: `index.html` title, `package.json` name, LandingPage / home / App copy say pktx.
* `.mcp.example.json` server name/command use `pktx`.
* `make check` passes for backend and frontend after the rename.

### R2 - Infra renamed with documented migration

Terraform reflects the new name; the actual AWS/Neon/Clerk migration is manual and
documented (renames force resource replacement — that is a human-gated apply, not CI).

* `infra/` uses `pktx-${environment}` function name, `/pktx/<env>` SSM prefix, `PKTX_*` Lambda env vars.
* No `terraform apply` is run by this item — apply steps live in the manual checklist.
* Comments/examples inside `infra/` reference pktx paths.

### R3 - Open-source hygiene

Repo is presentable to outside contributors.

* `LICENSE` added (MIT, current year, Nathan Hadzariga) — flag at PR for owner confirmation.
* `CONTRIBUTING.md` added: dev setup (uv, npm, make targets), test/lint commands, branch + conventional-commit conventions, PR expectations.
* `README.md` rewritten for a public audience: what pktx is, quickstart (docker compose + local), MCP client setup, env var table, link to docs/ and CONTRIBUTING.
* `docs/` reviewed: `architecture-notes.md` and `deployment.md` updated for pktx names; stale content pruned.
* `AGENTS.md` / `CLAUDE.md` / `gemini.md` updated to pktx (paths, commands, env vars).

### R4 - Manual rename checklist

Everything the repo cannot rename itself is written down as an ordered runbook.

* `docs/rename-checklist.md` covers: GitHub repo rename (+ remote URL update, redirect note), Neon project/database rename, Clerk app name + redirect URIs, AWS SSM params re-create under `/pktx/...`, Lambda function replacement via terraform apply, ECR/image names if applicable, local dir rename + `uv sync` re-install, MCP client config updates (Claude Desktop etc.), and updating any secrets/CI vars.
* Each step states the blast radius (what breaks until it is done).

### Out of scope

* Historical records stay untouched: `specs/0*` feature specs, `specs/lite/0*-plan.md` older plans, `specs/roadmap.md`, git history.
* No dual-support/deprecation shims for old env var names or CLI name.
* No actual terraform apply, GitHub/Neon/Clerk changes — manual checklist only.
* No new docs site, badges/CI shields polish beyond README rewrite.


## Design

Rename is mechanical but ordered; correctness hinges on the Python package move and the
env-var sweep staying in lockstep with infra and docs.

Order of operations:

1. `git mv backend/src/persona backend/src/pktx`, then sweep imports (`from persona`, `import persona`, `persona.`) and `pyproject.toml`.
2. Env-var sweep `PERSONA_` → `PKTX_` (code reads them in `config.py`, `auth.py`, `server.py`; tests set them; compose/Dockerfile/infra/docs reference them).
3. Branding + packaging sweep (compose, Dockerfile, frontend, .mcp.example.json, Makefiles).
4. Infra sweep (names, SSM paths, env map) — code-only, no apply.
5. Docs: README rewrite, CONTRIBUTING, LICENSE, rename-checklist, AGENTS/CLAUDE/gemini.
6. Leftover audit: `grep -ri persona` excluding `specs/`, `node_modules`, locks, `.git` must return only intentional hits (e.g., historical references in rename-checklist).

Verification: `make check` (backend pytest + ruff + pyright, frontend eslint + vitest),
`docker compose config` sanity, and a local `uv run pktx` boot smoke test.


## Tasks

### P1 - Code rename

Python package, env vars, packaging, compose, frontend.

- [x] T01 `git mv backend/src/persona backend/src/pktx`; update `pyproject.toml` (name, entry point, packages) and all Python imports in src + tests
- [x] T02 Rename all `PERSONA_*` env vars to `PKTX_*` in backend code, tests, `.env.example`, `docker-compose.yml`, `Dockerfile`
- [x] T03 Update docker-compose service + Postgres credentials/DB to pktx; update `.mcp.example.json`; check root/backend/frontend Makefiles and Dockerfile for persona references
- [x] T04 Frontend branding: `index.html`, `package.json`, LandingPage, home page, App — pktx naming/copy
- [x] T05 `make check` green (backend + frontend); `uv run pktx` boots locally

### P2 - Infra rename (code only)

- [x] T06 `infra/`: `pktx-${environment}` lambda name, `/pktx/<env>` SSM paths, `PKTX_*` env map, comments/examples; `terraform fmt`/`validate` if available locally

### P3 - Docs + open-source prep

- [x] T07 Rewrite `README.md` for public audience; update `docs/architecture-notes.md`, `docs/deployment.md`, `AGENTS.md`, `CLAUDE.md`, `gemini.md`
- [x] T08 Add `LICENSE` (MIT) and `CONTRIBUTING.md`
- [x] T09 Write `docs/rename-checklist.md` — ordered manual runbook (GitHub, Neon, Clerk, AWS SSM/Lambda, local machines, MCP clients) with blast radius per step
- [x] T10 Leftover audit: `grep -ri persona` outside `specs/`/locks returns only intentional hits; fix stragglers


### Implementation Notes

* Do T01 and T02 in one pass per file where they overlap — avoid a half-renamed state that
  breaks imports mid-review.
* `oauth_store.py` Fernet key salt deliberately keeps the `persona-oauth-kv` prefix
  (renaming it would rotate the key and invalidate all encrypted `oauth_kv` rows) — kept
  with an explanatory comment; no data migration needed.
* Divergences from plan (all done): Terraform state bucket/table names in `backend.tf` +
  `bootstrap.sh` also renamed — runbook step 3 covers `terraform init -migrate-state`;
  `uv.lock` + `package-lock.json` regenerated for the new package names;
  `.specify/memory/constitution.md` and `.gemini/policies/gemini-permissions.toml` swept
  too; root `make check` also passed checkov (66 passed, 0 failed).
* Local Postgres volume from compose keeps old `persona` credentials; note in
  rename-checklist that local dev needs `docker compose down -v` (data loss OK locally).
* `specs/lite/roadmap.md` and this plan keep the word "persona" legitimately (historical
  context) — the audit in T10 excludes `specs/`.
* GitHub repo rename gives automatic redirects for git remotes but not for badges/links —
  checklist should call that out.
