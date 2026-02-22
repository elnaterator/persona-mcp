data "aws_caller_identity" "current" {}

# ECR repository for the application container image
resource "aws_ecr_repository" "app" {
  #checkov:skip=CKV_AWS_136:Default AWS-managed encryption is sufficient for a personal app; KMS CMK adds cost/complexity without meaningful benefit
  #checkov:skip=CKV_AWS_51:Mutable image tags are required for the dev/prod deployment workflow (same :latest or :sha tag is re-pushed per environment)
  name                 = "persona-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.tags
}

# IAM role assumed by the Lambda function at runtime
resource "aws_iam_role" "lambda_exec" {
  name = "persona-${var.environment}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

# Allow Lambda to pull its container image from ECR
resource "aws_iam_role_policy" "ecr_pull" {
  name = "ecr-pull"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
        ]
        Resource = aws_ecr_repository.app.arn
      },
      {
        # ecr:GetAuthorizationToken cannot be scoped to a repository ARN
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      }
    ]
  })
}

# Allow Lambda to read application secrets from SSM Parameter Store
resource "aws_iam_role_policy" "ssm_read" {
  name = "ssm-read"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.ssm_parameter_prefix}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
        ]
        # AWS-managed SSM key; resource scope not supported for alias/aws/ssm
        Resource = "arn:aws:kms:${var.aws_region}:${data.aws_caller_identity.current.account_id}:key/alias/aws/ssm"
      }
    ]
  })
}

# AWS-managed policy granting CloudWatch Logs write access
resource "aws_iam_role_policy_attachment" "cw_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function running the application as a container image
resource "aws_lambda_function" "app" {
  #checkov:skip=CKV_AWS_50:X-Ray tracing deferred to future — adds cost/complexity not warranted for a personal app (research Decision 4)
  #checkov:skip=CKV_AWS_117:No VPC required for a personal app with no private resources to isolate
  #checkov:skip=CKV_AWS_116:No DLQ required — Lambda errors are surfaced via CloudWatch alarm; async retry not applicable to synchronous HTTP workload
  #checkov:skip=CKV_AWS_272:Code signing not warranted for a personal app; images are built and pushed by the developer directly
  #checkov:skip=CKV_AWS_115:No reserved concurrency limit set — personal app with low traffic; limiting concurrency would cause avoidable throttling
  #checkov:skip=CKV2_AWS_75:Open CORS is intentional — app must be accessible from any browser origin and MCP clients
  function_name = "persona-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.app.repository_url}:${var.image_tag}"
  architectures = ["x86_64"]
  memory_size   = var.memory_size
  timeout       = var.timeout

  tags = var.tags
}

# Public HTTPS endpoint for the Lambda function (no auth at URL level;
# Clerk JWT validation is enforced by the application on every request)
resource "aws_lambda_function_url" "app" {
  #checkov:skip=CKV_AWS_258:AuthType=NONE is intentional — IAM auth is incompatible with browser and MCP clients; Clerk JWT validation enforces auth at the app layer
  function_name      = aws_lambda_function.app.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["*"]
    allow_headers = ["*"]
  }
}
