output "bucket_name" {
  description = "Name of the backup bucket, or empty when backups are disabled."
  value       = var.backups_enabled ? aws_s3_bucket.backups[0].id : ""
}

output "bucket_arn" {
  description = "ARN of the backup bucket, or empty when backups are disabled."
  value       = var.backups_enabled ? aws_s3_bucket.backups[0].arn : ""
}
