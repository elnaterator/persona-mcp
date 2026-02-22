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
