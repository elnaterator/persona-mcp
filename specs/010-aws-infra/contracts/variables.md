# Terraform Variable Contracts: 010-aws-infra

**Date**: 2026-02-21

This document defines the complete input variable contract for each Terraform module and environment root. It serves as the authoritative reference for what each module accepts and validates.

---

## Environment Root (`infra/dev/` and `infra/prod/`)

These variables are declared in `variables.tf` and populated via `terraform.tfvars`.

```hcl
variable "environment" {
  description = "Environment name. Used as a suffix in all resource names."
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be 'dev' or 'prod'."
  }
}

variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-west-2"
}

variable "image_tag" {
  description = "ECR image tag for the Lambda function to run."
  type        = string
  default     = "latest"
}

variable "memory_size" {
  description = "Lambda function memory allocation in MB."
  type        = number
  default     = 512
  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 10240
    error_message = "memory_size must be between 128 and 10240 MB."
  }
}

variable "timeout" {
  description = "Lambda function timeout in seconds."
  type        = number
  default     = 30
  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "timeout must be between 1 and 900 seconds."
  }
}

variable "log_retention_days" {
  description = "Number of days to retain Lambda CloudWatch logs."
  type        = number
  default     = 14
  # Valid values: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365
}

variable "error_threshold" {
  description = "Number of Lambda errors in one period to trigger the CloudWatch alarm."
  type        = number
  default     = 1
}
```

---

## Module: `infra/modules/lambda`

```hcl
variable "environment" {
  description = "Environment name (dev or prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region."
  type        = string
}

variable "image_tag" {
  description = "ECR image tag for Lambda to run."
  type        = string
}

variable "memory_size" {
  description = "Lambda memory in MB."
  type        = number
  default     = 512
}

variable "timeout" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 30
}

variable "ssm_parameter_prefix" {
  description = "SSM parameter path prefix for this environment (e.g., /persona/dev)."
  type        = string
}

variable "tags" {
  description = "AWS resource tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}
```

---

## Module: `infra/modules/observability`

```hcl
variable "environment" {
  description = "Environment name (dev or prod)."
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to monitor."
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 14
}

variable "error_threshold" {
  description = "Lambda error count threshold to trigger alarm."
  type        = number
  default     = 1
}

variable "alarm_period_seconds" {
  description = "CloudWatch alarm evaluation window in seconds."
  type        = number
  default     = 300
}

variable "tags" {
  description = "AWS resource tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}
```
