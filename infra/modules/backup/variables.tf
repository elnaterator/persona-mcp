variable "environment" {
  description = "Deployment environment name (dev, prod)."
  type        = string
}

variable "backups_enabled" {
  description = "Create the backup bucket. Set false to opt an environment out of backups."
  type        = bool
  default     = true
}

variable "retention_days" {
  description = "Days to keep a backup object before expiring it."
  type        = number
  default     = 30
}

variable "noncurrent_retention_days" {
  description = "Days to keep a noncurrent (overwritten) backup version."
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}
