# providers.tf

terraform {
  # Note here that required_version is declared differently.
  # It means that the required version of Terraform is >=1.0 and <2.0.
  required_version = "~> 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# default provider configuration
provider "aws" {
  region = "us-east-1"
}

# provider alias with another region
provider "aws" {
  alias  = "us_west_2"
  region = "us-west-2"
}