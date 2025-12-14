terraform {
  required_version = ">= 1.6.0"

  required_providers {
    # This module can work with various automation platforms
    # Home Assistant, Node-RED, etc.
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}
