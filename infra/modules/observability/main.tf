# CloudWatch Log Group for Lambda function logs.
# Must be created before the Lambda function to ensure the retention policy
# is set from the start (otherwise Lambda auto-creates the group with no retention).
resource "aws_cloudwatch_log_group" "lambda" {
  #checkov:skip=CKV_AWS_338:1-year retention is cost-prohibitive for a personal app; 7–14 days is sufficient for debugging (research Decision 4)
  #checkov:skip=CKV_AWS_158:KMS CMK encryption for log groups adds cost/complexity without meaningful benefit for a personal app
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# CloudWatch alarm that fires when Lambda error count >= threshold in one period.
# treat_missing_data = notBreaching prevents spurious alarms when the function
# has not been invoked (no data points in the evaluation window).
resource "aws_cloudwatch_metric_alarm" "errors" {
  alarm_name          = "${var.lambda_function_name}-errors"
  alarm_description   = "Lambda error rate for ${var.lambda_function_name} exceeded threshold"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = var.alarm_period_seconds
  statistic           = "Sum"
  threshold           = var.error_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = var.tags
}
