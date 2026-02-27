output "log_group_name" {
  description = "CloudWatch Log Group name."
  value       = aws_cloudwatch_log_group.lambda.name
}

output "error_alarm_arn" {
  description = "ARN of the Lambda error CloudWatch alarm."
  value       = aws_cloudwatch_metric_alarm.errors.arn
}
