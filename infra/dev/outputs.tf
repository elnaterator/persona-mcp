output "ecr_repository_url" {
  description = "Full ECR repository URL. Use this for 'docker build' and 'docker push' commands."
  value       = module.lambda.ecr_repository_url
}

output "lambda_function_name" {
  description = "Lambda function name. Use to invoke the function via AWS CLI."
  value       = module.lambda.lambda_function_name
}

output "lambda_function_url" {
  description = "Public HTTPS endpoint for the application (Lambda Function URL)."
  value       = module.lambda.lambda_function_url
}

output "lambda_function_arn" {
  description = "Lambda function ARN."
  value       = module.lambda.lambda_function_arn
}

output "log_group_name" {
  description = "CloudWatch Log Group name for viewing Lambda logs."
  value       = module.observability.log_group_name
}
