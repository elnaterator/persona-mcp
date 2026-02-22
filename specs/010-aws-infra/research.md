# Research: AWS Infrastructure as Code (010-aws-infra)

**Date**: 2026-02-21
**Branch**: `010-aws-infra`

---

## Decision 1: Lambda HTTP Trigger & Runtime Packaging

**Decision**: AWS Lambda Web Adapter + Docker container image on ECR + Lambda Function URL

**Rationale**:
- The existing Dockerfile (multi-stage, Python 3.11, port 8000) requires **zero code changes** — the Lambda Web Adapter acts as a proxy between Lambda events and the app's localhost:8000
- Lambda Function URL avoids the cost and complexity of API Gateway for a personal app
- Container images on Lambda support up to 10 GB, accommodate the full Python environment + uv dependencies + frontend dist

**How it works**:
```dockerfile
# Single additional line in the runtime stage of Dockerfile
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter
# And set the correct port (app already exposes 8000):
ENV PORT=8000
```
The adapter performs an HTTP GET readiness check to `http://127.0.0.1:8000/` (via `AWS_LWA_READINESS_CHECK_PATH`) every 10ms until the app responds, then starts forwarding Lambda events as HTTP requests.

**Alternatives considered**:
- API Gateway HTTP API + Mangum adapter: adds cost and requires app-side adapter library
- API Gateway REST API: higher cost, more configuration, overkill for personal app
- Lambda Function URL with IAM auth: incompatible with browser and MCP clients
- Application Load Balancer: adds significant cost, overkill

---

## Decision 2: Multi-Environment Structure

**Decision**: Separate directories (`infra/dev/`, `infra/prod/`) with shared modules (`infra/modules/`)

**Rationale**:
- Separate directories provide hard isolation between environments: separate state files, separate backend configs, separate `terraform init` contexts
- Any mistake in dev cannot accidentally affect prod (no workspace `terraform workspace select` error risk)
- Each environment's backend block can point to a different S3 bucket/key
- CI matrix strategy maps cleanly: `matrix: environment: [dev, prod]` → `cd infra/${{ matrix.environment }}`

**Directory layout**:
```
infra/
├── modules/
│   ├── lambda/          # Lambda fn + ECR repo + Function URL + IAM role
│   └── observability/   # CloudWatch log group + error alarm
├── dev/
│   ├── main.tf          # Calls modules with dev-specific vars
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   ├── backend.tf       # S3 bucket: persona-terraform-state-dev
│   └── terraform.tfvars
└── prod/
    ├── main.tf          # Calls modules with prod-specific vars
    ├── variables.tf
    ├── outputs.tf
    ├── provider.tf
    ├── backend.tf       # S3 bucket: persona-terraform-state-prod
    └── terraform.tfvars
```

**Alternatives considered**:
- Terraform Workspaces: rejected — `workspace select` errors can cause cross-environment accidents; harder to audit in CI; doesn't support different backend configs per env

---

## Decision 3: Secrets Management

**Decision**: SSM Parameter Store (SecureString) with `lifecycle { ignore_changes = [value] }` placeholder pattern

**Rationale**:
- Terraform creates the SSM parameter with the correct name, type, and KMS encryption key, but with a placeholder value
- Developer sets the real value manually: `aws ssm put-parameter --name /persona/dev/database_url --value "..." --type SecureString --overwrite`
- `lifecycle { ignore_changes = [value] }` prevents Terraform from ever reverting the developer-set value
- Secret value is **never** in Terraform state, plan output, or version control
- Lambda reads parameters at startup via `boto3` SDK call (not environment variables)

**SSM path convention**: `/{app}/{env}/{param_name}`
- `/persona/dev/database_url` — Neon dev connection string
- `/persona/dev/clerk_secret_key` — Clerk dev secret key
- `/persona/prod/database_url` — Neon prod connection string
- `/persona/prod/clerk_secret_key` — Clerk prod secret key

**IAM scope**: Lambda execution role gets `ssm:GetParameter` + `kms:Decrypt` on `arn:aws:ssm:*:*:parameter/persona/{env}/*` only.

**Alternatives considered**:
- AWS Secrets Manager: higher cost (~$0.40/secret/month), rotation features not needed
- Lambda env vars set at apply time: values appear in plan output and Terraform state (even if encrypted at rest)
- No Terraform management: Terraform loses track of parameter existence; harder to audit

---

## Decision 4: Observability

**Decision**: CloudWatch Log Group (14-day retention) + CloudWatch error alarm (≥1 error in 5 minutes)

**Rationale**:
- Lambda automatically writes logs to CloudWatch Logs when a log group exists; Terraform-managed log group ensures retention policy is set before Lambda is created
- 14-day retention balances debugging usefulness against storage cost for a personal app
- Error alarm threshold: ≥1 error in a 5-minute window — appropriate for a personal app where even one error is notable
- No SNS topic defined (alarm state visible in CloudWatch console; overhead of email setup not worth it for personal app)

**Alarm configuration**:
- Namespace: `AWS/Lambda`
- Metric: `Errors`
- Statistic: `Sum`
- Period: 300s (5 min)
- Evaluation periods: 1
- Threshold: 1 (≥1 error triggers ALARM)
- treat_missing_data: `notBreaching`

**Alternatives considered**:
- X-Ray tracing: useful for distributed tracing but adds cost and complexity; deferred to future
- External monitoring (Datadog, New Relic): overkill and cost-prohibitive for personal app
- No alarm: silent failures; rejected

---

## Decision 5: CI Pipeline Design

**Decision**: New `.github/workflows/terraform-ci.yml` with Checkov + `hashicorp/setup-terraform@v3` + OIDC auth + matrix plan for dev/prod

**Key choices**:
- **Security scanner**: Checkov (not tfsec — tfsec was deprecated into Trivy in 2024; Checkov is actively maintained with broad policy library)
- **AWS auth**: OIDC (`aws-actions/configure-aws-credentials@v4` with `role-to-assume`) — no long-lived secrets, tokens expire after each job
- **Trigger**: `on: pull_request` only (path-filtered to `infra/**`) — no push trigger since there is no apply step
- **Job structure**:
  1. `terraform-validate` job: fmt check → Checkov → init → validate (runs once against `infra/`)
  2. `terraform-plan` job (matrix dev/prod, needs validate): init → plan (no output to logs to avoid secret leak)
- **Secret leak prevention**: `terraform plan -out=tfplan` saves binary plan file; `-no-color` flag used; SSM values are never fetched during plan (only paths/names are known to Terraform)
- **IAM for plan**: Read-only permissions on Lambda, ECR, SSM, CloudWatch, S3 state bucket, DynamoDB locks table

**OIDC trust policy pattern**: One IAM role per environment (`github-actions-terraform-dev`, `github-actions-terraform-prod`), trusted by the GitHub OIDC provider with condition `repo:owner/persona:*`.

**Alternatives considered**:
- tfsec: deprecated, migrated to Trivy
- Access key secrets: long-lived credentials; security risk
- Run plan on push to main: no apply exists anyway; plan-on-PR is sufficient for review

---

## Decision 6: Dockerfile Change for Lambda Web Adapter

**Discovery**: The app Dockerfile exposes port 8000 and runs `python -m persona.server`. The Lambda Web Adapter requires one additional COPY line in the runtime stage of the Dockerfile.

**Required Dockerfile addition** (in the final stage, before CMD):
```dockerfile
# Lambda Web Adapter — bridges Lambda events to the app's localhost:8000
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter
ENV AWS_LWA_PORT=8000
```

The `AWS_LWA_PORT` env var (preferred over `PORT`) tells the adapter which port to proxy to. The existing `EXPOSE 8000` and `HEALTHCHECK` remain valid; the adapter's internal readiness check uses this same port.

**Note**: The Dockerfile change is a **code task** (not Terraform), but Terraform's ECR definition and Lambda image_uri reference the image built from this updated Dockerfile.

---

## Decision 7: Remote State Backend

**Decision**: S3 + DynamoDB, one backend per environment, both bootstrapped manually before first `terraform init`

**Configuration pattern** (per environment):
```hcl
terraform {
  backend "s3" {
    bucket         = "persona-terraform-state-{env}"
    key            = "{env}/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "persona-terraform-locks-{env}"
    encrypt        = true
  }
}
```

**Bootstrap steps** (one-time, manual, before any `terraform init`):
1. Create S3 bucket with versioning + server-side encryption
2. Create DynamoDB table with `LockID` (String) as partition key
3. Repeat for both dev and prod

These resources are intentionally NOT managed by Terraform (avoids chicken-and-egg bootstrap problem).

---

## Discovery: ECR Authentication for Lambda

Lambda must be able to pull from ECR at invocation time. The Lambda execution role needs:
```hcl
actions = [
  "ecr:GetDownloadUrlForLayer",
  "ecr:BatchGetImage",
]
```
Additionally, ECR requires `ecr:GetAuthorizationToken` on `*` (not resource-scoped). This is a known AWS requirement for Lambda + ECR.

The ECR repository policy must also grant Lambda service access (or the execution role ARN) to pull images.
