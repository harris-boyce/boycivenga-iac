terraform {
  required_version = ">= 1.6.0"

  required_providers {
    unifi = {
      source  = "paultyng/unifi"
      version = "~> 0.41"
    }
  }
}
