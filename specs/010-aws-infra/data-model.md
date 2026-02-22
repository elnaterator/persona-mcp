# Infrastructure Resource Model: 010-aws-infra

**Date**: 2026-02-21
**Branch**: `010-aws-infra`

This document describes the Terraform resource graph — the infrastructure entities, their attributes, and their relationships. It is the infrastructure equivalent of a data model.

---

## Resource Graph Overview

```
Environment (dev | prod)
│
├── ECR Repository
│   └── (image pushed manually by developer)
│
├── IAM Role (Lambda execution)
│   ├── IAM Policy: ECR pull
│   ├── IAM Policy: SSM read + KMS decrypt
│   └── IAM Policy: CloudWatch Logs write (AWS managed)
│
├── SSM Parameters (SecureString)
│   ├── /persona/{env}/database_url
│   └── /persona/{env}/clerk_secret_key
│
├── Lambda Function
│   ├── image_uri → ECR Repository
│   ├── role → IAM Role
│   ├── environment vars (SSM parameter paths, not values)
│   └── CloudWatch Log Group (explicit Terraform resource)
│
├── Lambda Function URL
│   └── function → Lambda Function
│
└── CloudWatch Alarm
    └── dimension → Lambda Function name
```

---

## Module: `infra/modules/lambda`

### Purpose
Defines the ECR repository, Lambda function (container image), Lambda Function URL, and IAM execution role for one environment.

### Input Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `environment` | `string` | yes | Environment name (`dev` or `prod`) |
| `aws_region` | `string` | yes | AWS region (e.g., `us-west-2`) |
| `image_tag` | `string` | yes | ECR image tag for Lambda to run (e.g., `latest`) |
| `memory_size` | `number` | no | Lambda memory in MB (default: `512`) |
| `timeout` | `number` | no | Lambda timeout in seconds (default: `30`) |
| `ssm_parameter_paths` | `list(string)` | yes | SSM parameter paths the function needs to read |
| `tags` | `map(string)` | no | AWS resource tags (default: `{}`) |

### Resources Defined

| Terraform Resource | AWS Resource | Key Attributes |
|-------------------|--------------|----------------|
| `aws_ecr_repository.app` | ECR repository | `name = "persona-{env}"`, `image_tag_mutability = MUTABLE`, `scan_on_push = true` |
| `aws_iam_role.lambda_exec` | IAM role | `assume_role_policy` for `lambda.amazonaws.com` |
| `aws_iam_role_policy.ecr_pull` | IAM inline policy | `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`, `ecr:GetAuthorizationToken` |
| `aws_iam_role_policy.ssm_read` | IAM inline policy | `ssm:GetParameter`, `ssm:GetParameters`, `kms:Decrypt` on SSM paths |
| `aws_iam_role_policy_attachment.cw_logs` | AWS managed policy attachment | `AWSLambdaBasicExecutionRole` (CloudWatch Logs write) |
| `aws_lambda_function.app` | Lambda function | `package_type = Image`, `image_uri`, `memory_size`, `timeout`, `architectures = ["x86_64"]` |
| `aws_lambda_function_url.app` | Lambda Function URL | `authorization_type = "NONE"`, CORS config |

### Outputs

| Output | Description |
|--------|-------------|
| `ecr_repository_url` | Full ECR repository URL (for `docker push` in runbook) |
| `lambda_function_name` | Lambda function name (for console access and alarm dimensions) |
| `lambda_function_arn` | Lambda function ARN |
| `lambda_function_url` | Public HTTPS endpoint (Lambda Function URL) |

---

## Module: `infra/modules/observability`

### Purpose
Defines the CloudWatch Log Group (with retention) and CloudWatch error alarm for one Lambda function.

### Input Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `environment` | `string` | yes | Environment name (`dev` or `prod`) |
| `lambda_function_name` | `string` | yes | Name of the Lambda function to monitor |
| `log_retention_days` | `number` | no | CloudWatch log retention in days (default: `14`) |
| `error_threshold` | `number` | no | Error count to trigger alarm (default: `1`) |
| `alarm_period_seconds` | `number` | no | Evaluation window in seconds (default: `300`) |
| `tags` | `map(string)` | no | AWS resource tags (default: `{}`) |

### Resources Defined

| Terraform Resource | AWS Resource | Key Attributes |
|-------------------|--------------|----------------|
| `aws_cloudwatch_log_group.lambda` | CloudWatch Log Group | `name = /aws/lambda/{function_name}`, `retention_in_days = 14` |
| `aws_cloudwatch_metric_alarm.errors` | CloudWatch Alarm | `metric_name = Errors`, `namespace = AWS/Lambda`, `threshold = 1`, `period = 300`, `statistic = Sum` |

### Outputs

| Output | Description |
|--------|-------------|
| `log_group_name` | CloudWatch Log Group name |
| `error_alarm_arn` | CloudWatch alarm ARN |

---

## SSM Parameters (per environment)

These resources live in the environment root (not in a module) because they are environment-specific secrets, not reusable infrastructure components.

| Parameter Path | Type | Terraform Attribute | Description |
|---------------|------|---------------------|-------------|
| `/persona/{env}/database_url` | `SecureString` | `lifecycle { ignore_changes = [value] }` | Neon PostgreSQL connection string |
| `/persona/{env}/clerk_secret_key` | `SecureString` | `lifecycle { ignore_changes = [value] }` | Clerk backend API secret key |
| `/persona/{env}/clerk_publishable_key` | `SecureString` | `lifecycle { ignore_changes = [value] }` | Clerk frontend publishable key |

**Pattern**: Terraform creates each parameter with `value = "TO_BE_SET"` and `ignore_changes = [value]`. Developer sets the real value via AWS CLI before first apply of the Lambda function.

---

## State Backend Resources (bootstrapped manually, not in Terraform)

| AWS Resource | Dev | Prod |
|-------------|-----|------|
| S3 bucket (state storage) | `persona-terraform-state-dev` | `persona-terraform-state-prod` |
| S3 bucket settings | versioning enabled, SSE-S3 encryption | versioning enabled, SSE-S3 encryption |
| DynamoDB table (state locking) | `persona-terraform-locks-dev` | `persona-terraform-locks-prod` |
| DynamoDB partition key | `LockID` (String) | `LockID` (String) |

---

## Environment Root Variable Summary (per `terraform.tfvars`)

| Variable | Dev value | Prod value |
|----------|-----------|------------|
| `environment` | `"dev"` | `"prod"` |
| `aws_region` | `"us-west-2"` | `"us-west-2"` |
| `image_tag` | `"latest"` | `"latest"` |
| `memory_size` | `512` | `512` |
| `timeout` | `30` | `30` |
| `log_retention_days` | `7` | `14` |
| `error_threshold` | `1` | `1` |

---

## Resource Naming Convention

All resources use the pattern `persona-{environment}-{resource-type}`:

| Resource | Dev name | Prod name |
|----------|----------|-----------|
| ECR repository | `persona-dev` | `persona-prod` |
| Lambda function | `persona-dev` | `persona-prod` |
| IAM role | `persona-dev-lambda-exec` | `persona-prod-lambda-exec` |
| CloudWatch Log Group | `/aws/lambda/persona-dev` | `/aws/lambda/persona-prod` |
| CloudWatch Alarm | `persona-dev-lambda-errors` | `persona-prod-lambda-errors` |
| SSM parameter prefix | `/persona/dev/` | `/persona/prod/` |
