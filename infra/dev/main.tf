# Observability must be created before the Lambda function to ensure the CloudWatch
# Log Group exists with the correct retention policy before Lambda can auto-create
# an unretained one on first invocation.
module "observability" {
  source = "../modules/observability"

  environment          = var.environment
  lambda_function_name = "persona-${var.environment}"
  log_retention_days   = var.log_retention_days
  error_threshold      = var.error_threshold

  tags = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

module "lambda" {
  source = "../modules/lambda"

  environment          = var.environment
  aws_region           = var.aws_region
  image_tag            = var.image_tag
  memory_size          = var.memory_size
  timeout              = var.timeout
  ssm_parameter_prefix = "/persona/${var.environment}"

  tags = {
    environment = var.environment
    managed_by  = "terraform"
  }

  depends_on = [module.observability]
}

# SSM SecureString parameters for runtime secrets.
# Terraform creates each parameter with a placeholder value. Real values must be
# set manually before the first full terraform apply (see quickstart.md Step 4):
#   aws ssm put-parameter --name /persona/dev/database_url --value "..." \
#     --type SecureString --overwrite
#
# lifecycle.ignore_changes = [value] prevents Terraform from reverting
# developer-set values on subsequent applies.

resource "aws_ssm_parameter" "database_url" {
  #checkov:skip=CKV_AWS_337:Default AWS-managed SSM key (alias/aws/ssm) is sufficient; KMS CMK adds recurring cost without meaningful benefit for a personal app
  name  = "/persona/${var.environment}/database_url"
  type  = "SecureString"
  value = "TO_BE_SET"

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "aws_ssm_parameter" "clerk_secret_key" {
  #checkov:skip=CKV_AWS_337:Default AWS-managed SSM key (alias/aws/ssm) is sufficient; KMS CMK adds recurring cost without meaningful benefit for a personal app
  name  = "/persona/${var.environment}/clerk_secret_key"
  type  = "SecureString"
  value = "TO_BE_SET"

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "aws_ssm_parameter" "clerk_publishable_key" {
  #checkov:skip=CKV_AWS_337:Default AWS-managed SSM key (alias/aws/ssm) is sufficient; KMS CMK adds recurring cost without meaningful benefit for a personal app
  name  = "/persona/${var.environment}/clerk_publishable_key"
  type  = "SecureString"
  value = "TO_BE_SET"

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    environment = var.environment
    managed_by  = "terraform"
  }
}
