terraform {
  backend "s3" {
    bucket         = "pktx-terraform-state-prod"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "pktx-terraform-locks-prod"
    encrypt        = true
  }
}
