# SSM Parameter Schema: 010-aws-infra

**Date**: 2026-02-21

This document defines the SSM Parameter Store schema — the paths, types, and descriptions of all secrets the application reads at runtime. This is the "secrets contract" between the infrastructure and the application.

---

## Parameter Path Convention

```
/{app}/{environment}/{parameter_name}
```

- `{app}` = `persona` (fixed)
- `{environment}` = `dev` or `prod`
- `{parameter_name}` = snake_case parameter identifier

---

## Parameters

| Path | Type | KMS | Description | How to set |
|------|------|-----|-------------|------------|
| `/persona/{env}/database_url` | `SecureString` | AWS managed | Neon PostgreSQL connection string (full `postgresql://user:pass@host/db?sslmode=require`) | `aws ssm put-parameter --name /persona/{env}/database_url --value "..." --type SecureString --overwrite` |
| `/persona/{env}/clerk_secret_key` | `SecureString` | AWS managed | Clerk backend secret key (starts with `sk_`) | `aws ssm put-parameter --name /persona/{env}/clerk_secret_key --value "sk_..." --type SecureString --overwrite` |
| `/persona/{env}/clerk_publishable_key` | `SecureString` | AWS managed | Clerk frontend publishable key (starts with `pk_`) | `aws ssm put-parameter --name /persona/{env}/clerk_publishable_key --value "pk_..." --type SecureString --overwrite` |

---

## Terraform State Behavior

- Terraform creates each parameter with `value = "TO_BE_SET"` on first `terraform apply`
- `lifecycle { ignore_changes = [value] }` prevents Terraform from ever reverting the developer-set value
- The **parameter name and type** are Terraform-managed; the **value** is developer-managed
- SSM SecureString values are **never** stored in Terraform state or plan output

---

## IAM Access Granted to Lambda

The Lambda execution role receives the following policy:

```hcl
# Read all persona parameters for this environment
ssm:GetParameter, ssm:GetParameters
Resource: arn:aws:ssm:us-west-2:{account}:parameter/persona/{env}/*

# Decrypt KMS-encrypted values (AWS managed key)
kms:Decrypt, kms:DescribeKey
Resource: arn:aws:kms:us-west-2:{account}:key/alias/aws/ssm
```

---

## Application Startup Sequence

1. Lambda cold start: Lambda Web Adapter starts and waits for app readiness
2. `persona.server` starts → reads SSM parameters on startup via `boto3.client('ssm').get_parameter()`
3. App passes readiness check → Lambda Web Adapter begins forwarding events
4. App processes requests with secrets cached in memory (not re-fetched per request)

---

## Developer Setup Checklist (per environment)

Before running `terraform apply` for a new environment, set all parameter values:

```bash
# Replace {env} with dev or prod
# Replace values with real secrets from Neon and Clerk dashboards

aws ssm put-parameter \
  --region us-west-2 \
  --name /persona/{env}/database_url \
  --value "postgresql://user:pass@ep-xxx.us-west-2.aws.neon.tech/neondb?sslmode=require" \
  --type SecureString \
  --overwrite

aws ssm put-parameter \
  --region us-west-2 \
  --name /persona/{env}/clerk_secret_key \
  --value "sk_test_..." \
  --type SecureString \
  --overwrite

aws ssm put-parameter \
  --region us-west-2 \
  --name /persona/{env}/clerk_publishable_key \
  --value "pk_test_..." \
  --type SecureString \
  --overwrite
```

Verify parameters are set:
```bash
aws ssm get-parameters-by-path \
  --region us-west-2 \
  --path /persona/{env}/ \
  --with-decryption \
  --query "Parameters[*].{Name:Name,Type:Type}"
```
