# Plan 026 - ChatGPT connector support (hosted redirect allowlist + setup docs)

Date: 2026-08-22

Connecting pktx from ChatGPT failed at `/authorize` with *"Redirect URI
'https://chatgpt.com/connector/oauth/<id>' does not match allowed patterns"*: plan 025
shipped `PKTX_EXTRA_CLIENT_REDIRECT_URIS` but nothing sets it, and loopback-only is the
default. Wire the value through Terraform, allowlist ChatGPT's two callback shapes, and
refresh the ChatGPT setup steps in the UI connect panel and README.

## Requirements

### R1 - ChatGPT callbacks are allowlisted

* `https://chatgpt.com/connector/oauth/<connector-id>` (per-connector, needs a wildcard)
  passes redirect validation.
* `https://chatgpt.com/connector_platform_oauth_redirect` (fixed platform callback)
  passes too.
* Lookalike hosts (`chatgpt.com.evil.test`) and other paths on the same host are
  rejected.
* Loopback clients keep working unchanged.

### R2 - Deployment wiring

* `extra_client_redirect_uris` Terraform variable feeds
  `PKTX_EXTRA_CLIENT_REDIRECT_URIS` in dev and prod.
* Value lives in `terraform.tfvars`, not SSM — it is configuration, not a secret.
* Empty list yields an empty env var, which the resolver reads as loopback-only.

### R3 - Current ChatGPT setup instructions

* Connect panel shows the post-rename path: Settings → Apps → Advanced settings →
  Developer mode, then Plugins → Create.
* Panel calls out the plan requirement, the admin gate on Business/Enterprise, that the
  description is model-visible, and that older builds say Connectors.
* README documents the same steps plus the allowlist env var and the exact error it
  fixes.

## Design

The allowlist is one list shared by DCR and CIMD clients (plan 025), so a single
tfvars entry covers however ChatGPT chooses to register. FastMCP's matcher compares
scheme/host/port/path separately and rejects userinfo and dot-segments, so
`https://chatgpt.com/connector/oauth/*` cannot be widened by a crafted URI; verified
against the real failing URL and a lookalike host.

`notes?: string[]` is added to the connect panel's `Assistant` shape rather than
special-casing ChatGPT in JSX — ChatGPT is the only entry needing prose today, and the
next hosted client will need the same slot.

## Tasks

### P1 - Allowlist

- [x] T01 `extra_client_redirect_uris` variable + env wiring in `infra/dev`, `infra/prod`.
- [x] T02 ChatGPT patterns in both `terraform.tfvars`.
- [x] T03 Unit tests: both callback shapes allowed, lookalike host and stray path
      rejected, loopback unaffected.

### P2 - Instructions

- [x] T04 Connect panel: ChatGPT path updated, `notes` rendered under the snippet.
- [x] T05 Connect panel tests (default snippet, ChatGPT steps, notes, no-notes case).
- [x] T06 README ChatGPT section + `.env.example` example value.

### Implementation Notes

Requires `make deploy ENV=prod` to take effect — the Lambda reads the pattern list from
its environment at startup.

Sources for the ChatGPT UI path disagree (Apps vs Connectors vs Plugins) because of the
July 2026 rename; the panel leads with Plugins and names Connectors as the older label.
