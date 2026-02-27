# Terraform Output Contracts: 010-aws-infra

**Date**: 2026-02-21

This document defines what each environment root exposes as Terraform outputs — the "response schema" of the infrastructure. These values are visible after `terraform apply` and are needed for the manual provisioning runbook.

---

## Environment Root Outputs (`infra/dev/outputs.tf`, `infra/prod/outputs.tf`)

```hcl
output "ecr_repository_url" {
  description = "Full ECR repository URL. Use this for 'docker build' and 'docker push' commands."
  value       = module.lambda.ecr_repository_url
}

output "lambda_function_name" {
  description = "Lambda function name. Use to invoke the function via AWS CLI."
  value       = module.lambda.lambda_function_name
}

output "lambda_function_url" {
  description = "Public HTTPS endpoint for the application (Lambda Function URL)."
  value       = module.lambda.lambda_function_url
}

output "lambda_function_arn" {
  description = "Lambda function ARN."
  value       = module.lambda.lambda_function_arn
  sensitive   = false
}

output "log_group_name" {
  description = "CloudWatch Log Group name for viewing Lambda logs."
  value       = module.observability.log_group_name
}
```

---

## Module Outputs

### `infra/modules/lambda/outputs.tf`

```hcl
output "ecr_repository_url" {
  description = "ECR repository URL (account.dkr.ecr.region.amazonaws.com/name)."
  value       = aws_ecr_repository.app.repository_url
}

output "lambda_function_name" {
  description = "Lambda function name."
  value       = aws_lambda_function.app.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN."
  value       = aws_lambda_function.app.arn
}

output "lambda_function_url" {
  description = "Lambda Function URL (public HTTPS endpoint)."
  value       = aws_lambda_function_url.app.function_url
}

output "lambda_exec_role_arn" {
  description = "ARN of the Lambda execution IAM role."
  value       = aws_iam_role.lambda_exec.arn
}
```

### `infra/modules/observability/outputs.tf`

```hcl
output "log_group_name" {
  description = "CloudWatch Log Group name."
  value       = aws_cloudwatch_log_group.lambda.name
}

output "error_alarm_arn" {
  description = "ARN of the Lambda error CloudWatch alarm."
  value       = aws_cloudwatch_metric_alarm.errors.arn
}
```
