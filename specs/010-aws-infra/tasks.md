# Tasks: AWS Infrastructure as Code

**Input**: Design documents from `/specs/010-aws-infra/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Feature**: Deploy Persona app to AWS Lambda (container image + ECR) via Terraform with dev/prod environments, SSM secrets, CloudWatch observability, and CI validation (lint + Checkov + plan). No `terraform apply` in CI ever.

**Tests**: No test tasks — spec.md does not request automated test files. Terraform validation is exercised via `terraform fmt`, `terraform validate`, `terraform plan`, and Checkov as part of the CI workflow itself.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Directory Structure & Non-Terraform Changes)

**Purpose**: Create the `infra/` directory skeleton and apply non-Terraform changes to existing project files required by all subsequent phases.

- [x] T001 Create infra/ directory structure with empty placeholder files: infra/modules/lambda/.gitkeep, infra/modules/observability/.gitkeep, infra/dev/.gitkeep, infra/prod/.gitkeep
- [x] T002 [P] Add Lambda Web Adapter to Dockerfile runtime stage (final stage, before EXPOSE 8000): `COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter` and `ENV AWS_LWA_PORT=8000`
- [x] T003 [P] Add tf-lint and tf-check targets to root Makefile: tf-lint runs `terraform fmt -check -recursive` from infra/; tf-check runs tf-lint then `checkov -d infra/ --quiet --compact`; also update the existing `check` target to depend on `tf-lint` so `make check` remains the single pre-commit verification command (constitution requirement)

---

## Phase 2: Foundational (Shared Terraform Modules)

**Purpose**: Implement the reusable `lambda` and `observability` modules. Both `infra/dev/` and `infra/prod/` environment roots source these modules — they MUST exist before any environment root can be written or validated.

**⚠️ CRITICAL**: Environment roots (US1) and CI validation (US2) cannot begin until this phase is complete.

- [x] T004 Create infra/modules/lambda/variables.tf declaring: environment (string), aws_region (string), image_tag (string), memory_size (number, default 512), timeout (number, default 30), ssm_parameter_prefix (string), tags (map(string), default {}) per contracts/variables.md
- [x] T005 [P] Create infra/modules/lambda/outputs.tf declaring: ecr_repository_url, lambda_function_name, lambda_function_arn, lambda_function_url, lambda_exec_role_arn per contracts/outputs.md
- [x] T006 [P] Create infra/modules/observability/variables.tf declaring: environment (string), lambda_function_name (string), log_retention_days (number, default 14), error_threshold (number, default 1), alarm_period_seconds (number, default 300), tags (map(string), default {}) per contracts/variables.md
- [x] T007 [P] Create infra/modules/observability/outputs.tf declaring: log_group_name, error_alarm_arn per contracts/outputs.md
- [x] T008 Create infra/modules/lambda/main.tf with: aws_ecr_repository.app (name="persona-${var.environment}", scan_on_push=true, image_tag_mutability=MUTABLE), aws_iam_role.lambda_exec (assume_role_policy for lambda.amazonaws.com), aws_iam_role_policy.ecr_pull (ecr:GetDownloadUrlForLayer + ecr:BatchGetImage + ecr:GetAuthorizationToken on *), aws_iam_role_policy.ssm_read (ssm:GetParameter + ssm:GetParameters + kms:Decrypt + kms:DescribeKey on ${var.ssm_parameter_prefix}/*), aws_iam_role_policy_attachment.cw_logs (AWSLambdaBasicExecutionRole), aws_lambda_function.app (package_type=Image, architectures=["x86_64"], memory_size=var.memory_size, timeout=var.timeout, image_uri="${aws_ecr_repository.app.repository_url}:${var.image_tag}"), aws_lambda_function_url.app (authorization_type="NONE", CORS allow all origins)
- [x] T009 Create infra/modules/observability/main.tf with: aws_cloudwatch_log_group.lambda (name="/aws/lambda/${var.lambda_function_name}", retention_in_days=var.log_retention_days), aws_cloudwatch_metric_alarm.errors (metric_name=Errors, namespace=AWS/Lambda, statistic=Sum, period=var.alarm_period_seconds, evaluation_periods=1, threshold=var.error_threshold, comparison_operator=GreaterThanOrEqualToThreshold, treat_missing_data=notBreaching, dimensions={FunctionName=var.lambda_function_name})

**Checkpoint**: Modules complete — environment root implementation (US1) can now begin in parallel for dev and prod.

---

## Phase 3: User Story 1 — Define and Review Infrastructure Code (Priority: P1) 🎯 MVP

**Goal**: Create fully plan-able, validated Terraform code for both dev and prod environments. A developer can run `terraform init && terraform plan` in either environment directory and receive a correct, complete execution plan showing the expected ~10 resources.

**Independent Test**: Run `terraform fmt -check -recursive` from `infra/` (zero violations) → `cd infra/dev && terraform init && terraform validate` (success) → `terraform plan` (plan shows ~10 expected resources). Repeat for `infra/prod`. No AWS credentials or live resources required for validate; plan requires OIDC or static credentials.

### Implementation for User Story 1

- [x] T010 [P] [US1] Create infra/dev/provider.tf with terraform block (required_version=">=1.7", required_providers hashicorp/aws ~5.x) and provider "aws" block (region=var.aws_region)
- [x] T011 [P] [US1] Create infra/prod/provider.tf with terraform block (required_version=">=1.7", required_providers hashicorp/aws ~5.x) and provider "aws" block (region=var.aws_region)
- [x] T012 [P] [US1] Create infra/dev/backend.tf with terraform backend "s3" block (bucket="persona-terraform-state-dev", key="dev/terraform.tfstate", region="us-west-2", dynamodb_table="persona-terraform-locks-dev", encrypt=true)
- [x] T013 [P] [US1] Create infra/prod/backend.tf with terraform backend "s3" block (bucket="persona-terraform-state-prod", key="prod/terraform.tfstate", region="us-west-2", dynamodb_table="persona-terraform-locks-prod", encrypt=true)
- [x] T014 [P] [US1] Create infra/dev/variables.tf declaring: environment (string, validation: must be dev or prod), aws_region (string, default "us-west-2"), image_tag (string, default "latest"), memory_size (number, default 512, validation 128-10240), timeout (number, default 30, validation 1-900), log_retention_days (number, default 14), error_threshold (number, default 1)
- [x] T015 [P] [US1] Create infra/prod/variables.tf with identical declarations to infra/dev/variables.tf (same contract, same validations)
- [x] T016 [P] [US1] Create infra/dev/terraform.tfvars with: environment="dev", aws_region="us-west-2", image_tag="latest", memory_size=512, timeout=30, log_retention_days=7, error_threshold=1
- [x] T017 [P] [US1] Create infra/prod/terraform.tfvars with: environment="prod", aws_region="us-west-2", image_tag="latest", memory_size=512, timeout=30, log_retention_days=14, error_threshold=1
- [x] T018 [P] [US1] Create infra/dev/outputs.tf exposing: ecr_repository_url (from module.lambda), lambda_function_name (from module.lambda), lambda_function_url (from module.lambda), lambda_function_arn (from module.lambda), log_group_name (from module.observability) per contracts/outputs.md
- [x] T019 [P] [US1] Create infra/prod/outputs.tf exposing same outputs as infra/dev/outputs.tf (ecr_repository_url, lambda_function_name, lambda_function_url, lambda_function_arn, log_group_name)
- [x] T020 [US1] Create infra/dev/main.tf: module "observability" (source="../modules/observability", environment=var.environment, lambda_function_name="persona-${var.environment}", log_retention_days=var.log_retention_days, error_threshold=var.error_threshold); module "lambda" (source="../modules/lambda", environment=var.environment, aws_region=var.aws_region, image_tag=var.image_tag, memory_size=var.memory_size, timeout=var.timeout, ssm_parameter_prefix="/persona/${var.environment}", depends_on=[module.observability]); aws_ssm_parameter resources for /persona/dev/database_url, /persona/dev/clerk_secret_key, /persona/dev/clerk_publishable_key (each: type="SecureString", value="TO_BE_SET", lifecycle { ignore_changes=[value] })
- [x] T021 [P] [US1] Create infra/prod/main.tf with identical structure to infra/dev/main.tf but referencing /persona/prod/* SSM paths (same module sources, same pattern, environment variable drives naming)
- [x] T022 [US1] Run `terraform fmt -recursive` from infra/ to canonically format all HCL files written in T004-T021 (fix any formatting deviations before CI catches them)

**Checkpoint**: US1 complete. `terraform fmt -check` and `terraform validate` both pass in each environment directory. US2 (CI workflow) can now be implemented.

---

## Phase 4: User Story 2 — Automated CI Validation on Every PR (Priority: P2)

**Goal**: Create a GitHub Actions workflow that automatically runs lint, Checkov security scan, and `terraform plan` for both dev and prod on every PR touching `infra/**`. No `terraform apply` command exists anywhere in the workflow.

**Independent Test**: Open a PR with a deliberate formatting error in any `.tf` file → the `terraform-validate` CI job fails with a clear format violation message. Fix formatting → CI passes. Grep the workflow file for `terraform apply` → zero matches (SC-005).

### Implementation for User Story 2

- [x] T023 [US2] Create .github/workflows/terraform-ci.yml with trigger `on: pull_request: paths: ['infra/**']` and `terraform-lint-scan` job (named to match what it actually does — fmt check + security scan, not terraform validate): steps: actions/checkout@v4, hashicorp/setup-terraform@v3 (terraform_version: "~1.7"), `terraform fmt -check -recursive` run from infra/, `pip install checkov` then `checkov -d infra/ --quiet --compact`; add a comment at top of file stating no terraform apply steps exist
- [x] T024 [US2] Add `terraform-plan` matrix job to .github/workflows/terraform-ci.yml: needs=[terraform-lint-scan], strategy.matrix.environment=[dev, prod], timeout-minutes=10, steps: actions/checkout@v4, hashicorp/setup-terraform@v3, aws-actions/configure-aws-credentials@v4 (role-to-assume: secrets.TF_PLAN_ROLE_DEV or TF_PLAN_ROLE_PROD matching matrix.environment, aws-region: us-west-2), `terraform -chdir=infra/${{matrix.environment}} init`, `terraform -chdir=infra/${{matrix.environment}} plan -no-color`; **PREREQUISITE**: GitHub repo secrets `TF_PLAN_ROLE_DEV` and `TF_PLAN_ROLE_PROD` must be set to the ARNs of the OIDC IAM roles (`github-actions-terraform-dev`, `github-actions-terraform-prod`) before this CI job can authenticate — see quickstart.md Prerequisites Step 4 for OIDC provider setup

**Checkpoint**: US2 complete. Confirm zero `terraform apply` commands in .github/workflows/terraform-ci.yml (SC-005).

---

## Phase 5: User Story 3 — Manual Provisioning Documentation (Priority: P3)

**Goal**: Ensure a developer can clone the repository and find everything needed to manually provision either environment within 5 minutes. Confirm no CI automation ever executes `terraform apply`.

**Independent Test**: Grep all files in `.github/workflows/` for `terraform apply` → zero matches. Read README.md infrastructure section — it references quickstart.md and lists prerequisites. A developer following quickstart.md can produce a full `terraform plan` without additional context.

### Implementation for User Story 3

- [x] T025 [US3] Add an "## Infrastructure" section to README.md documenting: the infra/ directory purpose, required tools (Terraform 1.7+, AWS CLI 2.x, Docker), a note that no apply runs in CI, and a reference to specs/010-aws-infra/quickstart.md for the full manual provisioning runbook
- [x] T026 [US3] Audit all files under .github/workflows/ using grep for `terraform apply` and confirm zero matches; add a comment block at the top of .github/workflows/terraform-ci.yml explicitly documenting that no apply step exists (satisfying SC-005 auditability)

**Checkpoint**: US3 complete. All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final infrastructure hygiene, format gate, and security validation.

- [x] T027 [P] Create infra/.gitignore with Terraform-generated files: `.terraform/`, `*.tfstate`, `*.tfstate.backup`, `tfplan`, `*.tfplan` — NOTE: do NOT ignore `.terraform.lock.hcl`; this provider lock file must be committed to ensure consistent provider versions across developer and CI environments
- [x] T028 Run `terraform fmt -check -recursive` from infra/ as a final gate — confirm zero violations after all HCL files are written
- [x] T029 [P] Verify Checkov passes locally: `uvx checkov -d infra/ --quiet --compact` — confirm no high-severity findings before opening a PR (uvx fetches checkov automatically; no pip install needed)
- [x] T030 [P] Update .github/workflows/terraform-ci.yml to replace the `pip install checkov` + `checkov` steps with `astral-sh/setup-uv@v4` (installs uv on the runner) followed by `uvx checkov -d infra/ --quiet --compact` — aligns CI with the project-wide uv dependency management policy

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T002 and T003 are parallel to T001
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS US1 and US2
- **US1 (Phase 3)**: Depends on Phase 2 (modules must exist); dev and prod roots can be created in parallel
- **US2 (Phase 4)**: Depends on Phase 2 (valid TF code required for CI to validate); can overlap with Phase 3 if desired
- **US3 (Phase 5)**: Depends on Phase 4 (CI workflows must exist to be audited for no-apply)
- **Polish (Phase 6)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 Foundational — no dependency on US2/US3
- **US2 (P2)**: Starts after Phase 2 Foundational — independent of US1 environment roots (can be written while US1 progresses)
- **US3 (P3)**: Starts after Phase 4 (audit requires CI workflow to exist)

### Within Each Phase

- T004 + T005 + T006 + T007 are all parallel (different files, different modules)
- T008 depends on T004 + T005 (lambda main.tf uses variables and outputs)
- T009 depends on T006 + T007 (observability main.tf uses variables and outputs)
- T008 and T009 are parallel to each other (different module directories)
- T010–T019 are all parallel (different files across dev/ and prod/)
- T020 and T021 are parallel to each other; both depend on T010–T019 and T008+T009
- T022 depends on T020 + T021 (formats all written files)
- T024 depends on T023 (adds to the same workflow file)

---

## Parallel Example: Phase 2 (Foundational Modules)

```
# Wave 1 — all four in parallel:
T004: infra/modules/lambda/variables.tf
T005: infra/modules/lambda/outputs.tf
T006: infra/modules/observability/variables.tf
T007: infra/modules/observability/outputs.tf

# Wave 2 — parallel to each other (after wave 1):
T008: infra/modules/lambda/main.tf      (needs T004 + T005)
T009: infra/modules/observability/main.tf  (needs T006 + T007)
```

## Parallel Example: Phase 3 (US1 Environment Roots)

```
# Wave 1 — all ten in parallel (after modules complete):
T010: infra/dev/provider.tf         T011: infra/prod/provider.tf
T012: infra/dev/backend.tf          T013: infra/prod/backend.tf
T014: infra/dev/variables.tf        T015: infra/prod/variables.tf
T016: infra/dev/terraform.tfvars    T017: infra/prod/terraform.tfvars
T018: infra/dev/outputs.tf          T019: infra/prod/outputs.tf

# Wave 2 — parallel to each other (after wave 1 complete):
T020: infra/dev/main.tf             T021: infra/prod/main.tf

# Wave 3 — sequential (after T020 + T021):
T022: terraform fmt -recursive
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational — lambda + observability modules (T004–T009)
3. Complete Phase 3: US1 — dev + prod environment roots (T010–T022)
4. **STOP and VALIDATE**: Run `terraform fmt -check && terraform validate` in both env directories
5. A complete, reviewable, plan-able Terraform codebase is delivered — US1 MVP done

### Incremental Delivery

1. Phase 1 + Phase 2 → Terraform modules ready
2. Phase 3 (US1) → Plan-able infrastructure → **MVP delivered**
3. Phase 4 (US2) → CI automation active; PRs self-validate
4. Phase 5 (US3) → Runbook + audit → Developer-ready for manual apply
5. Phase 6 (Polish) → Format gate + Checkov → Production-ready

### Single Developer Strategy

With one developer, implement phases sequentially:
1. Setup → Modules → Dev env root → Prod env root → CI → Docs → Polish
2. Write `infra/dev/` first; use it as a reference when writing `infra/prod/`
3. Run `terraform fmt` after every file to catch formatting issues early; don't wait until T022

---

## Notes

- **No `terraform apply` ever in CI** — guard rail enforced by T026 audit and plan.md constraint FR-010/SC-005
- **Secret values are never written to .tf or .tfvars** — SSM placeholder pattern (`value = "TO_BE_SET"`, `lifecycle { ignore_changes = [value] }`) only (FR-012)
- **Bootstrap resources (S3 + DynamoDB for state) are NOT Terraform-managed** — see quickstart.md Prerequisites Step 2; never add them to any .tf file
- **Lambda module depends_on observability module** — log group must be created before Lambda to prevent AWS auto-creating an unretained log group (plan.md constraint #6)
- **ECR image must exist before Lambda function** can be created — the quickstart.md Step 3 (targeted apply) handles this; Terraform code should not work around it
- **quickstart.md already documents the full manual provisioning runbook** — US3 runbook requirement (FR-011) is satisfied by the existing quickstart.md; T025 adds a README pointer to it
- [P] tasks = different files, no shared state dependencies, safe to run concurrently
- [Story] label maps each task to a specific user story for traceability
- Commit after each logical group (e.g., after modules complete, after each env root is done)
- Run `terraform fmt -check -recursive` before every commit in infra/
