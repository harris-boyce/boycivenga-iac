# Primary Site Environment

This directory contains the Terraform configuration for the primary site/home network.

## Configuration

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your actual values:
   - UniFi Controller URL and credentials
   - WiFi passwords
   - Other site-specific settings

3. Initialize Terraform:
   ```bash
   terraform init
   ```

4. Review the plan:
   ```bash
   terraform plan
   ```

5. Apply the configuration:
   ```bash
   terraform apply
   ```

## Resources Managed

- **Ubiquiti Networks**: VLANs for Management, IoT, and Guest networks
- **Wireless Networks**: Main and guest WiFi configurations
- **Firewall Rules**: Network segmentation and security policies
- **Port Profiles**: Switch port configurations for APs and devices
- **Homebridge VM**: HomeKit integration server
- **Automations**: Smart home automation rules and scripts

## Network Layout

- **Management VLAN (10)**: `10.10.10.0/24` - Management devices
- **IoT VLAN (20)**: `10.10.20.0/24` - IoT devices
- **Guest VLAN (30)**: `10.10.30.0/24` - Guest network

## Security Considerations

- Never commit `terraform.tfvars` to version control
- Store credentials securely (use environment variables or secret managers)
- Review firewall rules before applying
- Test network changes during maintenance windows

## Outputs

After applying, you can view outputs with:
```bash
terraform output
```

Key outputs include:
- UniFi site ID and network IDs
- Homebridge URL
- Automation configuration summary
