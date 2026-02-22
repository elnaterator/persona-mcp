# Feature Specification: AWS Infrastructure as Code

**Feature Branch**: `010-aws-infra`
**Created**: 2026-02-21
**Status**: Draft
**Input**: User description: "I want to stand up infrastructure as code using terraform to deploy this app to AWS in us-west-2 region. I want to use neon as a postgres database and an aws lambda function for the main app. I want a dev and a prod environment. I want to define all the code and test using a plan, but claude should NOT provision the resources in AWS, this MUST be done manually by me. I want to have a linter and security check as part of the CI pipeline. The CI pipeline should validate the terraform code, but should NOT apply the changes (at least not yet)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define and Review Infrastructure Code (Priority: P1)

As a developer, I want all application infrastructure described in version-controlled code so that environment setup is reproducible, auditable, and reviewed before any resources are created.

**Why this priority**: Without this foundation, no other infrastructure story is possible. Code-defined infrastructure enables review, rollback, and consistency across environments.

**Independent Test**: Can be fully tested by examining the Terraform codebase for completeness and correctness, then running automated validation checks — delivering a reviewable, plan-able infrastructure definition without touching any live cloud accounts.

**Acceptance Scenarios**:

1. **Given** the Terraform codebase, **When** a developer runs the validation tool locally, **Then** the code reports zero errors and produces a human-readable execution plan showing what would be created.
2. **Given** separate dev and prod configurations, **When** a developer targets either environment, **Then** only that environment's resources are planned, with no cross-contamination.
3. **Given** the defined code, **When** a security scanner runs, **Then** it reports no high-severity findings.

---

### User Story 2 - Automated CI Validation on Every Pull Request (Priority: P2)

As a developer, I want every pull request that touches infrastructure code to be automatically linted, security-scanned, and validated — without any live resources being created or modified — so that broken or insecure infrastructure definitions are caught before review.

**Why this priority**: CI validation is the safety net for infrastructure changes. It provides fast feedback and prevents obviously broken code from ever reaching a manual apply step.

**Independent Test**: Can be fully tested by opening a pull request containing a deliberate Terraform formatting error and a deliberate security misconfiguration, then confirming that CI blocks the PR with actionable failure messages for both issues.

**Acceptance Scenarios**:

1. **Given** a pull request modifying any Terraform file, **When** CI runs, **Then** lint, security, and validation checks all run automatically and complete with a clear pass/fail status.
2. **Given** a pull request with a formatting violation, **When** CI runs, **Then** the lint step fails and reports the specific violation with enough detail for the author to fix it.
3. **Given** a pull request with a security misconfiguration (e.g., overly permissive access), **When** CI runs, **Then** the security check fails and identifies the specific rule violated.
4. **Given** a pull request where all checks pass, **When** CI runs, **Then** no resources are created, modified, or destroyed in any AWS account or Neon project.
5. **Given** a pull request that CI validates, **When** the developer reviews CI output, **Then** they can see the proposed infrastructure changes (the plan) for both dev and prod environments.

---

### User Story 3 - Manual Provisioning by the Developer (Priority: P3)

As the developer-operator, I want to apply infrastructure changes manually using the Terraform code as a reference — never automatically — so that I retain full control over when resources are created or modified in each environment.

**Why this priority**: The explicit constraint is that no automation should provision resources. This story captures the human-driven workflow that CI enables but never replaces.

**Independent Test**: Can be fully tested by confirming that no CI job contains an "apply" step, and that the Terraform codebase includes documentation or runbook instructions for how to manually apply each environment.

**Acceptance Scenarios**:

1. **Given** the Terraform codebase and documented instructions, **When** the developer follows the runbook for the dev environment, **Then** they can provision all resources in the correct region without ambiguity.
2. **Given** a desire to update the prod environment, **When** the developer follows the prod runbook, **Then** only prod resources are affected; dev resources are untouched.
3. **Given** the CI pipeline configuration, **When** any CI job runs (on PR or merge), **Then** zero Terraform `apply` commands execute; no live resources are created or modified automatically.

---

### Edge Cases

- What happens when Terraform state is out of sync with actual cloud resources (state drift)?
- How does the system handle secrets (database credentials, API keys) needed at provision time without exposing them in code?
- What happens if the dev and prod environments have meaningfully different resource sizing or settings?
- How does a developer recover if infrastructure in one environment is accidentally destroyed?
- What happens when a CI check fails on the main branch after a merge?

## Clarifications

### Session 2026-02-21

- Q: How will the Lambda function receive HTTP traffic, and what runtime packaging strategy should be used? → A: AWS Lambda Web Adapter with Docker container image (ECR). The existing Dockerfile runs unchanged on Lambda; a single binary layer (Lambda Web Adapter) bridges Lambda events to the app's localhost port. Lambda Function URL provides the HTTPS endpoint — no API Gateway required. The deployment artifact is a container image pushed to ECR, not a ZIP package.
- Q: How should runtime secrets (Neon DB connection string, Clerk keys) be injected into the Lambda function? → A: AWS Systems Manager (SSM) Parameter Store using SecureString parameters. Terraform defines the parameter paths and grants the Lambda execution role read access. Secret values are set manually by the developer (via AWS console or CLI) before the first apply. Lambda reads parameter values at startup via SDK call — values are never stored in Terraform code or state.
- Q: What are the Lambda function's performance requirements (memory, timeout)? → A: 512 MB memory, 30 second timeout. Covers FastAPI cold-start time with container images, database queries, and MCP tool calls at low request volume.
- Q: What observability is required for the Lambda function in production? → A: CloudWatch Logs with a defined retention policy + a CloudWatch alarm on Lambda error rate. All resources Terraform-managed, native AWS, no additional services required.
- Q: Will the Lambda Function URL be publicly accessible or restricted at the network level? → A: Public (auth mode: NONE). The Lambda Function URL is publicly reachable; authentication is enforced entirely by the application's Clerk JWT validation on every endpoint. No network-level restriction at the Lambda URL layer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define all application infrastructure (compute, database connectivity, IAM permissions, container registry) using declarative Terraform code checked into version control.
- **FR-002**: Infrastructure MUST target the AWS us-west-2 region for all AWS resources.
- **FR-003**: The system MUST provide two fully isolated environment configurations: `dev` and `prod`, each independently plan-able and apply-able.
- **FR-004**: The application compute layer MUST be defined as an AWS Lambda function running a Docker container image, with the AWS Lambda Web Adapter included so the existing application code requires no changes. A Lambda Function URL with auth mode `NONE` provides the public HTTPS endpoint; application-layer Clerk JWT validation enforces authentication on every request. The function MUST be configured with 512 MB memory and a 30-second timeout.
- **FR-004a**: The system MUST define an Amazon ECR repository per environment to store the application container images that Lambda will execute.
- **FR-005**: The database layer MUST use Neon (managed PostgreSQL), with only the connection configuration stored in Terraform — not the database engine itself.
- **FR-006**: Terraform state MUST be stored remotely (not locally) to support future collaboration and prevent state loss.
- **FR-007**: The CI pipeline MUST automatically run Terraform lint checks on every pull request that modifies infrastructure code.
- **FR-008**: The CI pipeline MUST automatically run a static security scan against all Terraform code on every pull request.
- **FR-009**: The CI pipeline MUST automatically run Terraform validation (syntax check + plan) for both `dev` and `prod` environments on every pull request.
- **FR-010**: The CI pipeline MUST NOT execute any Terraform `apply` command under any circumstances (on PR, on merge, or on schedule).
- **FR-011**: The system MUST provide documented runbook instructions that a developer can follow to manually apply infrastructure changes for each environment.
- **FR-012**: Secrets and sensitive values (Neon database connection string, Clerk API keys) MUST be stored in AWS SSM Parameter Store as SecureString parameters. Terraform MUST define the parameter paths and grant the Lambda execution role read-only access. Secret values MUST be populated manually by the developer before apply — never in Terraform code, variable files, or version control.
- **FR-013**: The Lambda execution role MUST have a least-privilege IAM policy granting read access only to the specific SSM parameter paths used by the application.
- **FR-014**: The system MUST define a CloudWatch Log Group for each environment's Lambda function with an explicit log retention policy (to control cost).
- **FR-015**: The system MUST define a CloudWatch alarm per environment that triggers when the Lambda error rate exceeds a defined threshold, providing a signal that the function is failing in production.

### Key Entities

- **Environment**: A named configuration (`dev` or `prod`) that parameterizes resource names, sizing, and Neon project/branch references. Environments are fully isolated from each other.
- **Lambda Function**: The primary compute resource that hosts the application. Runs as a Docker container image with the AWS Lambda Web Adapter binary included. Exposed via a Lambda Function URL (HTTPS). Defined with its execution role, environment variables (referencing secrets), and ECR image source.
- **ECR Repository**: A per-environment container registry that stores the application Docker images. Lambda pulls images from ECR at invocation time.
- **Neon Database Connection**: Configuration that points the application to the correct Neon project and branch for each environment. The Neon project itself is provisioned externally (via Neon console or Terraform Neon provider).
- **Remote State Backend**: The mechanism for storing Terraform state files outside of the local filesystem, ensuring state is durable and shared.
- **IAM Role**: The execution identity granted to the Lambda function, scoped to the minimum permissions required for the application to operate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Terraform validation, lint, and security checks all pass with zero blocking errors on a clean pull request — verifiable by CI green status.
- **SC-002**: Dev and prod environments can each be independently planned without affecting the other — verifiable by targeting each workspace/directory and confirming only the expected resources appear in the plan.
- **SC-003**: A developer following the runbook can produce a complete Terraform execution plan for either environment within 5 minutes of cloning the repository, with no additional tribal knowledge required.
- **SC-004**: CI provides a complete validation result (lint + security + plan for both environments) within 10 minutes of a pull request being opened.
- **SC-005**: Zero Terraform `apply` commands exist in any CI job configuration — verifiable by automated audit of all CI pipeline files.
- **SC-006**: All sensitive values are sourced from a secrets management mechanism at apply time and produce no plaintext secrets in the plan output or state file.

## Assumptions

- The Neon PostgreSQL projects (dev and prod) will be created manually via the Neon console before infrastructure is first applied; Terraform will only manage connection configuration, not the Neon project lifecycle.
- AWS credentials for running `terraform plan` in CI will be supplied via environment secrets in the CI provider (e.g., GitHub Actions secrets), not committed to code.
- Remote Terraform state will be stored in an AWS S3 bucket with state locking via DynamoDB — both created manually before first use, consistent with standard AWS Terraform patterns.
- The Lambda deployment artifact is a Docker container image (not a ZIP package). The image is built by the existing build pipeline (`make build` / `docker build`) and pushed to ECR manually before a `terraform apply`; Terraform defines the ECR repository and Lambda configuration but does not build or push the image.
- A single AWS account is used for both dev and prod, differentiated by environment-prefixed resource names (e.g., `persona-dev-*`, `persona-prod-*`).
- The CI linter will be `terraform fmt -check`; the security scanner will be `tfsec` or `checkov` (industry-standard defaults for Terraform security scanning).
