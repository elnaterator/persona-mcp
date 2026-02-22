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
}

variable "error_threshold" {
  description = "Number of Lambda errors in one period to trigger the CloudWatch alarm."
  type        = number
  default     = 1
}
