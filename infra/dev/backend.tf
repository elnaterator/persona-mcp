terraform {
  backend "s3" {
    bucket         = "pktx-terraform-state-dev"
    key            = "dev/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "pktx-terraform-locks-dev"
    encrypt        = true
  }
}
