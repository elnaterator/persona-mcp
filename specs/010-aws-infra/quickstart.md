# Infrastructure Quickstart & Manual Provisioning Runbook

**Feature**: 010-aws-infra
**Date**: 2026-02-21

This runbook describes everything needed to manually provision the Persona application infrastructure in AWS. Claude will **never** execute these steps — they are always performed by the developer.

---

## Prerequisites (One-Time Setup)

Complete these steps once before provisioning any environment for the first time.

### 1. Install Required Tools

```bash
# Terraform (1.7+)
brew install terraform

# AWS CLI (2.x)
brew install awscli
aws configure  # or set AWS_PROFILE env var

# Docker (for building and pushing images)
# Already installed if using Docker Desktop
```

### 2. Bootstrap Remote State Infrastructure

Create the S3 buckets and DynamoDB tables for Terraform state. These are **not** managed by Terraform — they are created once manually.

```bash
# For dev environment
aws s3api create-bucket \
  --region us-west-2 \
  --bucket persona-terraform-state-dev \
  --create-bucket-configuration LocationConstraint=us-west-2

aws s3api put-bucket-versioning \
  --bucket persona-terraform-state-dev \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket persona-terraform-state-dev \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

aws dynamodb create-table \
  --region us-west-2 \
  --table-name persona-terraform-locks-dev \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Repeat for prod (replace 'dev' with 'prod')
```

### 3. Set Up SSM Parameters (Secrets)

Before applying Terraform, set the actual secret values for each environment. See `contracts/ssm-parameters.md` for the full setup commands.

**Do this before the first `terraform apply`** for each environment, otherwise the Lambda function will start but fail to read secrets.

### 4. Set Up OIDC for GitHub Actions CI (Optional)

If you want `terraform plan` to run in CI, create an IAM OIDC provider and role:

```bash
# Create OIDC provider for GitHub
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Create IAM role per environment (see infra/docs/iam-ci-role.json for trust policy)
# Grant read-only permissions: Lambda, ECR describe, SSM describe (no GetParameter), S3 state read
```

---

## Provisioning a New Environment

Follow these steps in order. Substitute `{env}` with `dev` or `prod`.

### Step 1: Initialize Terraform

```bash
cd infra/{env}
terraform init
```

Expected output: `Terraform has been successfully initialized!`

### Step 2: Review the Plan

```bash
terraform plan
```

Review the output carefully. Expected resources on first apply:
- `aws_ecr_repository.app` (persona-{env})
- `aws_iam_role.lambda_exec` (persona-{env}-lambda-exec)
- `aws_iam_role_policy.ecr_pull`
- `aws_iam_role_policy.ssm_read`
- `aws_iam_role_policy_attachment.cw_logs`
- `aws_ssm_parameter.database_url` (value: TO_BE_SET)
- `aws_ssm_parameter.clerk_secret_key` (value: TO_BE_SET)
- `aws_ssm_parameter.clerk_publishable_key` (value: TO_BE_SET)
- `aws_cloudwatch_log_group.lambda`
- `aws_cloudwatch_metric_alarm.errors`

**Note**: `aws_lambda_function` and `aws_lambda_function_url` are NOT in the first plan — they require an ECR image to exist first.

### Step 3: Apply Infrastructure (Excluding Lambda Function)

```bash
# Apply only the resources that don't require a container image yet
terraform apply -target=aws_ecr_repository.app \
                -target=aws_iam_role.lambda_exec \
                -target=aws_iam_role_policy.ecr_pull \
                -target=aws_iam_role_policy.ssm_read \
                -target=aws_iam_role_policy_attachment.cw_logs \
                -target=aws_ssm_parameter.database_url \
                -target=aws_ssm_parameter.clerk_secret_key \
                -target=aws_ssm_parameter.clerk_publishable_key \
                -target=module.observability.aws_cloudwatch_log_group.lambda
```

### Step 4: Set Real Secret Values

```bash
# Replace placeholder values set by Terraform with real secrets
aws ssm put-parameter \
  --region us-west-2 \
  --name /persona/{env}/database_url \
  --value "postgresql://..." \
  --type SecureString \
  --overwrite

# (See contracts/ssm-parameters.md for all three parameters)
```

### Step 5: Build and Push the Docker Image

```bash
# Get the ECR URL from Terraform output
ECR_URL=$(terraform output -raw ecr_repository_url)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Authenticate Docker to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com

# Build the image (from repo root — Dockerfile includes Lambda Web Adapter)
cd ../../  # back to repo root
docker build -t persona-{env}:latest .

# Tag and push to ECR
docker tag persona-{env}:latest ${ECR_URL}:latest
docker push ${ECR_URL}:latest
```

### Step 6: Apply the Full Infrastructure

```bash
cd infra/{env}
terraform apply
```

This creates the Lambda function and Function URL, referencing the ECR image pushed in Step 5.

### Step 7: Verify

```bash
# Get the public URL
terraform output lambda_function_url

# Test the health endpoint
curl $(terraform output -raw lambda_function_url)/health

# Expected: {"status": "ok", ...}
```

---

## Updating an Existing Environment

### Updating Infrastructure (Terraform Changes)

```bash
cd infra/{env}
terraform plan   # Review changes
terraform apply  # Apply after review
```

### Deploying a New Application Version (Docker Image Only)

No Terraform changes needed — just push a new image:

```bash
# Rebuild and push (from repo root)
docker build -t persona-{env}:latest .
docker tag persona-{env}:latest ${ECR_URL}:latest
docker push ${ECR_URL}:latest

# Force Lambda to use the new image
aws lambda update-function-code \
  --region us-west-2 \
  --function-name persona-{env} \
  --image-uri ${ECR_URL}:latest
```

---

## Destroying an Environment

**Warning**: This is irreversible. All AWS resources are deleted. State data and SSM parameter values are lost.

```bash
cd infra/{env}
terraform destroy
```

Note: The S3 state bucket and DynamoDB locks table are NOT destroyed by `terraform destroy` (they are not managed by Terraform). Delete them manually if needed.

---

## Verifying CI Checks Pass Locally

Before opening a PR, run the same checks that CI will run:

```bash
# From repo root
cd infra

# Format check (what CI runs)
terraform fmt -check -recursive

# Format fix
terraform fmt -recursive

# Security scan (install checkov if not already installed)
pip install checkov
checkov -d . --quiet --compact

# Validate each environment
cd dev && terraform init && terraform validate && cd ..
cd prod && terraform init && terraform validate && cd ..
```

---

## Troubleshooting

| Symptom | Likely cause | Resolution |
|---------|-------------|------------|
| Lambda returns 502 | App failed to start; Lambda Web Adapter never received readiness | Check CloudWatch logs: `aws logs tail /aws/lambda/persona-{env} --follow` |
| Lambda returns 500 | App started but errored on request | Check CloudWatch logs for Python traceback |
| Lambda cold start > 15s | SSM parameter reads timing out | Verify IAM role has `ssm:GetParameter` on `/persona/{env}/*` |
| `docker push` fails with "denied" | ECR auth token expired | Re-run `aws ecr get-login-password | docker login ...` |
| `terraform plan` fails "ECR image not found" | Image not yet pushed | Complete Step 5 (build and push) before full apply |
| CI plan fails "no identity" | OIDC role not set up | See Prerequisites Step 4 |
