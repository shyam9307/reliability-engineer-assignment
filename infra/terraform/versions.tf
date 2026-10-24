terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket       = "relassign-tfstate-819693014102-819693014102-ap-south-1-an"
    key          = "terraform.tfstate"
    region       = "ap-south-1"
    use_lockfile = true
    encrypt      = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-south-1"
}