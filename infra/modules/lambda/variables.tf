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
