terraform {
  backend "s3" {
    bucket         = "persona-terraform-state-prod"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "persona-terraform-locks-prod"
    encrypt        = true
  }
}
