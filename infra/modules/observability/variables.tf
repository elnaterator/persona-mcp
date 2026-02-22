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
