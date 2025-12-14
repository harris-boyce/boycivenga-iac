terraform {
  required_version = ">= 1.6.0"

  backend "local" {
    path = "terraform.tfstate"
  }

  required_providers {
    unifi = {
      source  = "paultyng/unifi"
      version = "~> 0.41"
    }
  }
}

provider "unifi" {
  api_url  = var.unifi_api_url
  username = var.unifi_username
  password = var.unifi_password
}
