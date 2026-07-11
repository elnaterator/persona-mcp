# Rename runbook: persona → pktx (external systems)

The repo itself is fully renamed in code (plan 019). Everything below lives *outside* the
repo and must be renamed by hand, in this order. Each step lists its blast radius — what is
broken until the step completes.

The one deliberate exception in code: the Fernet key salt in
`backend/src/pktx/oauth_store.py` keeps the historical `persona-oauth-kv` prefix so
existing encrypted OAuth state in the `oauth_kv` table stays readable. Do not "fix" it.

## 1. Local dev machines

**Blast radius:** none (local only).

- [ ] Rename the working dir: `mv ~/workspace/persona/persona-mcp ~/workspace/pktx` (or wherever yours lives).
- [ ] Re-create the venv install: `cd backend && uv sync` (package name changed `persona` → `pktx`).
- [ ] Reset the local compose stack: `docker compose down -v` — the old `pg-data` volume was initialized with `persona` credentials and the compose file now uses `pktx`. **Local data is lost**; export first if you care.
- [ ] Update any local MCP client config (`~/.claude.json`, `.cursor/mcp.json`, Claude Desktop) that registers the server under the name `persona`.

## 2. GitHub repository

**Blast radius:** none for git (GitHub redirects old remote URLs); badges, pinned links, and clones by other people keep working via redirect but should be updated.

- [ ] Rename the repo: Settings → General → rename `persona-mcp` → `pktx`.
- [ ] Update local remotes anyway (redirects are best-effort): `git remote set-url origin git@github.com:<owner>/pktx.git`.
- [ ] Update any external links to the repo (profile pins, resume, docs) — redirects do not rewrite rendered links or badges.
- [ ] If CI/CD or deploy keys reference the repo by name, re-check them after the rename.

## 3. Terraform remote state (per env: dev, then prod)

**Blast radius:** `terraform` commands fail from the moment `backend.tf` (already renamed in code) diverges from the real bucket, until migration completes. No runtime impact.

- [ ] Create the new state bucket + lock table: `./infra/bootstrap.sh <env>` (now provisions `pktx-terraform-state-<env>` / `pktx-terraform-locks-<env>`).
- [ ] Migrate state: `cd infra/<env> && terraform init -migrate-state`.
- [ ] Verify: `terraform plan` runs and shows only the expected rename-driven changes.
- [ ] After both envs migrate: delete the old `persona-terraform-*` buckets/tables (see step 8).

## 4. AWS SSM parameters (per env)

**Blast radius:** none until the Lambda apply in step 5 — the running `persona-<env>` Lambda keeps reading the old `/persona/...` paths. The new Lambda will read `/pktx/...`, so these must exist **before** step 5.

- [ ] Copy every parameter to the new prefix (values unchanged):
  ```bash
  for p in database_url clerk_secret_key clerk_publishable_key pktx_public_url \
           clerk_jwks_url clerk_issuer clerk_webhook_secret \
           clerk_oauth_client_id clerk_oauth_client_secret; do
    old="/persona/<env>/${p/pktx_public_url/persona_public_url}"
    aws ssm get-parameter --name "$old" --with-decryption --query Parameter.Value --output text | \
      xargs -I{} aws ssm put-parameter --name "/pktx/<env>/$p" --type SecureString --value {}
  done
  ```
  (Note the one key rename: `persona_public_url` → `pktx_public_url`.)
- [ ] Terraform manages these params — expect `terraform plan` to want to create/adopt them; import if needed to avoid value clobbering (`terraform import`).

## 5. AWS Lambda + ECR (per env)

**Blast radius:** downtime for the env from old-Lambda delete until DNS/clients point at the new Function URL. The function name change forces **replacement**, and the Function URL changes with it.

- [ ] Create the new ECR repo `pktx-<env>` (or let `make deploy ENV=<env>` / Terraform do it), build + push the image.
- [ ] `cd infra/<env> && terraform apply` — replaces `persona-<env>` with `pktx-<env>` (Lambda, IAM, log group, keep-warm rule).
- [ ] Grab the new Function URL from outputs; update DNS / any bookmark pointing at the old URL.
- [ ] Update `/pktx/<env>/pktx_public_url` in SSM if the public URL changed, and re-apply so the Lambda env picks it up.
- [ ] Smoke test: `curl https://<new-url>/health`, then a full MCP connect from a client.

## 6. Clerk

**Blast radius:** MCP sign-in breaks if the redirect URI no longer matches the public URL; REST/web auth unaffected by a pure display rename.

- [ ] Rename the Clerk application (display name) persona → pktx — cosmetic, shows on the sign-in screen.
- [ ] If the public URL changed in step 5: update the OAuth application's redirect URI to `<new PKTX_PUBLIC_URL>/auth/callback`.
- [ ] Verify the webhook endpoint URL (Clerk → Webhooks) points at the new public URL.

## 7. Neon (PostgreSQL)

**Blast radius:** none for a display rename; connection-string changes break the app until SSM is updated.

- [ ] Rename the Neon project (and database, if desired) persona → pktx in the Neon console.
- [ ] If the connection string changed (it can when the database/role is renamed): update `/pktx/<env>/database_url` in SSM and re-apply / restart.
- [ ] The `oauth_kv` data survives as-is — the Fernet salt was deliberately kept (see intro).

## 8. MCP clients (every machine that connected)

**Blast radius:** assistants lose the tool until re-added; stored server tokens survive only if the public URL did not change.

- [ ] Re-add the server under the new name/URL: `claude mcp add --transport http pktx https://<url>/mcp` (and the Cursor/Kiro/Copilot equivalents).
- [ ] If the public URL changed, clients must re-register and re-authorize (DCR registrations are bound to the old resource URL) — expect one browser sign-in per client.

## 9. Cleanup (after everything above is verified)

**Blast radius:** none if steps 1–8 are verified; irreversible.

- [ ] Delete old SSM params under `/persona/<env>/`.
- [ ] Delete the old `persona-<env>` ECR repos (images) — the Lambda replacement in step 5 already removed the old functions.
- [ ] Delete old Terraform state buckets `persona-terraform-state-*` and lock tables `persona-terraform-locks-*`.
- [ ] Search your password manager / notes for stale `persona` URLs and creds references.
