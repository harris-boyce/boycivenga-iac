# Secondary Site Environment

This directory contains the Terraform configuration for the secondary site/home network.

## Configuration

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your actual values

3. Initialize and apply:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## Resources Managed

- **Ubiquiti Networks**: VLANs for Management and IoT networks
- **Wireless Networks**: WiFi configuration
- **Firewall Rules**: Network segmentation and security policies
- **Automations**: Smart home automation rules

## Network Layout

- **Management VLAN (10)**: `10.20.10.0/24` - Management devices
- **IoT VLAN (20)**: `10.20.20.0/24` - IoT devices

Note: Different subnet range (10.20.x.x) from primary site to avoid conflicts.
