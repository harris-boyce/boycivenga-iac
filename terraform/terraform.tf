# Terraform and provider version constraints

terraform {
  required_version = ">= 1.0"

  required_providers {
    unifi = {
      source  = "ubiquiti-community/unifi"
      version = "0.41.4-beta2"
    }
  }

  # Backend configuration - using local backend for now
  # In production, this would use a remote backend like S3 or Terraform Cloud
  backend "local" {
    path = "terraform.tfstate"
  }
}
