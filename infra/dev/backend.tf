terraform {
  backend "s3" {
    bucket         = "persona-terraform-state-dev"
    key            = "dev/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "persona-terraform-locks-dev"
    encrypt        = true
  }
}
