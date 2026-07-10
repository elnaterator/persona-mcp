# Plan 018 - Lambda keep-warm EventBridge rule

Date: 2026-07-09

Branch: `build/018-lambda-keep-warm`

Cold starts hurt the MCP connect flow and first browser load. Add an EventBridge
scheduled rule that invokes the Lambda every 5 minutes with a synthetic
`GET /health` event, keeping one instance warm. Free tier; no backend changes.


## Requirements

### R1 - Scheduled warm ping

EventBridge rule pings the Lambda every 5 minutes so one execution environment
stays warm.

* `aws_cloudwatch_event_rule` with `schedule_expression = "rate(5 minutes)"` lives in `infra/modules/lambda`
* Rule target invokes the Lambda directly with a static input payload shaped like a Lambda Function URL event (API GW payload v2) for `GET /health` — Lambda Web Adapter translates it to a real HTTP request against the app
* `aws_lambda_permission` grants `events.amazonaws.com` invoke on the function, scoped to the rule ARN
* No Clerk credentials involved — `/health` is public and returns `{"status": "ok"}` without touching Postgres (verified in `backend/src/persona/api/routes.py`; no backend change needed)
* Toggle via module variable `keep_warm_enabled` (bool, default `true`) using `count` — lets an environment opt out without code changes
* Both `infra/dev` and `infra/prod` get the warmer automatically via the shared module; no per-env wiring beyond the (optional) variable

### R2 - Cost and hygiene

* Stays in free tier: EventBridge scheduled rules are free; ~8.6k extra invocations/month is far under the 1M free Lambda requests
* Warmer resources are tagged with the module's `tags` like every other resource
* `terraform fmt` clean; `terraform validate` passes in `infra/dev` and `infra/prod`


## Design

EventBridge classic rule (not EventBridge Scheduler) — no execution role needed;
Lambda targets use resource-based permissions, fewer moving parts.

Payload (static `input` on the target), minimal API GW v2 shape LWA accepts:

```json
{
  "version": "2.0",
  "routeKey": "$default",
  "rawPath": "/health",
  "rawQueryString": "",
  "headers": { "x-keep-warm": "true" },
  "requestContext": {
    "http": { "method": "GET", "path": "/health", "protocol": "HTTP/1.1", "sourceIp": "127.0.0.1", "userAgent": "keep-warm" }
  },
  "isBase64Encoded": false
}
```

Known accepted limits (single-user app): a concurrent second request and the
first request after a deploy are still cold.


## Tasks

### P1 - Terraform

- [x] T01 Add `keep_warm_enabled` variable (bool, default `true`) to `infra/modules/lambda/variables.tf`
- [x] T02 Add `aws_cloudwatch_event_rule` (rate 5 min), `aws_cloudwatch_event_target` (static `/health` v2 payload), and `aws_lambda_permission` (events.amazonaws.com, scoped to rule ARN) to `infra/modules/lambda/main.tf`, all behind `count = var.keep_warm_enabled ? 1 : 0`
- [x] T03 `terraform fmt -recursive infra/` and `terraform validate` in `infra/dev` and `infra/prod` — both pass
- [x] T04 Update AGENTS.md infra notes (one line under Infrastructure: keep-warm rule + toggle)


### Implementation Notes

- All changes in the shared module; dev/prod inherit on next apply. Do not run
  `terraform apply` as part of this item — user applies.
- Checkov runs in CI on infra; add `#checkov:skip` annotations only if a rule
  actually fires.
- Out of scope: provisioned concurrency, health-endpoint changes, splitting UI
  hosting, alarms on warmer failures.
