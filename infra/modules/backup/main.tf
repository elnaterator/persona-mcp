# Off-provider backup destination. Neon's PITR protects against a bad write;
# this bucket protects against losing the Neon account itself. The nightly
# dump is written here by the application Lambda (see modules/lambda).

resource "aws_s3_bucket" "backups" {
  #checkov:skip=CKV_AWS_144:Cross-region replication doubles storage cost for a personal app; a single-region versioned bucket is the accepted durability level
  #checkov:skip=CKV_AWS_18:Access logging would need a second bucket and log lifecycle for no operational benefit at this scale — S3 data events are available via CloudTrail if ever needed
  #checkov:skip=CKV2_AWS_62:Event notifications are not used — backup failures surface from the Lambda invocation, not the bucket
  #checkov:skip=CKV_AWS_145:Default AES256 (SSE-S3) is sufficient; a KMS CMK adds recurring cost without meaningful benefit for a personal app, matching the SSM parameters
  #checkov:skip=CKV_AWS_21:Versioning is enabled in aws_s3_bucket_versioning.backups — checkov cannot follow the count-indexed bucket reference
  #checkov:skip=CKV2_AWS_6:Public access is blocked in aws_s3_bucket_public_access_block.backups — checkov cannot follow the count-indexed bucket reference
  #checkov:skip=CKV2_AWS_61:Lifecycle rules are set in aws_s3_bucket_lifecycle_configuration.backups — checkov cannot follow the count-indexed bucket reference
  count = var.backups_enabled ? 1 : 0

  bucket        = "pktx-backups-${var.environment}"
  force_destroy = false

  tags = var.tags
}

resource "aws_s3_bucket_versioning" "backups" {
  count = var.backups_enabled ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  count = var.backups_enabled ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  count = var.backups_enabled ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "backups" {
  count = var.backups_enabled ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Deny any request that is not TLS — the bucket holds a full copy of every
# user's data.
resource "aws_s3_bucket_policy" "backups" {
  count = var.backups_enabled ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.backups[0].arn,
          "${aws_s3_bucket.backups[0].arn}/*",
        ]
        Condition = {
          Bool = { "aws:SecureTransport" = "false" }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.backups]
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  count = var.backups_enabled ? 1 : 0

  bucket = aws_s3_bucket.backups[0].id

  rule {
    id     = "expire-old-backups"
    status = "Enabled"

    # No prefix filter: the bucket holds nothing but backups, and an unfiltered
    # rule also covers stray multipart uploads.
    filter {}

    expiration {
      days = var.retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_retention_days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}
