# Terraform and provider version constraints

terraform {
  required_version = ">= 1.0"

  required_providers {
    unifi = {
      source  = "paultyng/unifi"
      version = "~> 0.41"
    }
  }
}
