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
  description = "SSM parameter path prefix for this environment (e.g., /pktx/dev)."
  type        = string
}

variable "environment_variables" {
  description = "Environment variables injected into the Lambda function at runtime."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "keep_warm_enabled" {
  description = "Whether the EventBridge keep-warm rule pings the Lambda every 5 minutes to avoid cold starts."
  type        = bool
  default     = true
}

variable "backup_bucket_arn" {
  description = "ARN of the backup bucket. Empty disables the nightly backup rule."
  type        = string
  default     = ""
}

variable "backup_token" {
  description = "Shared secret sent as x-pktx-backup-token by the backup rule. Empty disables the nightly backup rule."
  type        = string
  default     = ""
  sensitive   = true
}

variable "backup_schedule_expression" {
  description = "EventBridge schedule for the nightly database backup."
  type        = string
  default     = "cron(0 8 * * ? *)"
}

variable "tags" {
  description = "AWS resource tags applied to all resources in this module."
  type        = map(string)
  default     = {}
}
