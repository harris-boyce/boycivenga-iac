# Operational Runbook

This runbook provides step-by-step procedures for common operational tasks and incident response.

## Table of Contents

- [Getting Started](#getting-started)
- [Daily Operations](#daily-operations)
- [Deployment Procedures](#deployment-procedures)
- [Troubleshooting](#troubleshooting)
- [Disaster Recovery](#disaster-recovery)
- [Maintenance Tasks](#maintenance-tasks)
- [Emergency Procedures](#emergency-procedures)

## Getting Started

### Prerequisites

- Access to repository
- Terraform CLI installed
- Access to UniFi Controller
- GitHub account with appropriate permissions

### Quick Reference

**Repository URL**: `https://github.com/harris-boyce/boycivenga-iac`

**Key Contacts**:
- Repository Owner: harris-boyce
- Infrastructure Team: [Add contacts]

**Important Links**:
- [UniFi Controller (Primary)](https://unifi.example.com:8443)
- [Homebridge UI (Primary)](http://10.10.10.50:8581)
- [GitHub Actions](https://github.com/harris-boyce/boycivenga-iac/actions)

## Daily Operations

### Checking System Health

#### 1. Check GitHub Actions Status

```bash
# View recent workflow runs
gh run list --repo harris-boyce/boycivenga-iac --limit 10

# Check specific workflow
gh run view <run-id>
```

#### 2. Check Infrastructure Status

```bash
cd environments/site-primary
terraform plan -detailed-exitcode
```

**Exit codes**:
- 0: No changes
- 1: Error
- 2: Changes detected (drift)

#### 3. Monitor UniFi Controller

1. Log into UniFi Controller
2. Check device status (all should be "Connected")
3. Review alerts and notifications
4. Check client connectivity

### Reviewing Logs

#### GitHub Actions Logs

1. Navigate to Actions tab
2. Select workflow run
3. Review job logs
4. Download artifacts if needed

#### Terraform Logs

```bash
# Enable debug logging
export TF_LOG=DEBUG
export TF_LOG_PATH=./terraform.log

# Run operation
terraform plan

# Review logs
less terraform.log
```

## Deployment Procedures

### Standard Deployment Process

#### 1. Create Feature Branch

```bash
git checkout -b feature/description-of-change
```

#### 2. Make Configuration Changes

```bash
# Edit configuration files
vim environments/site-primary/site.tf

# Test locally
cd environments/site-primary
terraform init
terraform plan
```

#### 3. Commit and Push

```bash
git add .
git commit -m "feat: description of change"
git push origin feature/description-of-change
```

#### 4. Create Pull Request

1. Go to GitHub repository
2. Click "New Pull Request"
3. Fill out PR template
4. Request review

#### 5. Review and Merge

1. Review automated checks
2. Review Terraform plan in PR comments
3. Address feedback
4. Merge when approved

#### 6. Deploy Changes

1. Go to Actions tab
2. Select "Terraform Apply" workflow
3. Click "Run workflow"
4. Select environment
5. Confirm deployment

### Emergency Deployment

For urgent changes that can't wait for full review:

```bash
# Apply directly (use with extreme caution)
cd environments/site-primary
terraform apply -auto-approve

# Document in incident report
```

**Note**: Emergency deployments should be rare and followed by proper documentation.

## Troubleshooting

### Common Issues and Solutions

#### Issue: Terraform Plan Fails

**Symptoms**:
- `terraform plan` returns errors
- GitHub Actions workflow fails

**Diagnosis**:
```bash
cd environments/site-primary
terraform plan
```

**Common Causes & Solutions**:

1. **Authentication failure**
   ```bash
   # Verify credentials
   curl -k https://unifi.example.com:8443
   
   # Update credentials in terraform.tfvars
   vim terraform.tfvars
   ```

2. **State lock**
   ```bash
   # Check for lock file
   ls -la terraform.tfstate.lock.info
   
   # Force unlock (if safe)
   terraform force-unlock <LOCK_ID>
   ```

3. **Module not found**
   ```bash
   # Re-initialize
   terraform init -upgrade
   ```

#### Issue: UniFi Controller Unreachable

**Symptoms**:
- Terraform can't connect to controller
- Network devices show offline

**Diagnosis**:
```bash
# Test connectivity
ping unifi.example.com
curl -k https://unifi.example.com:8443

# Check DNS
nslookup unifi.example.com
```

**Solutions**:

1. **Verify controller is running**
   ```bash
   # SSH to controller host
   ssh admin@unifi.example.com
   
   # Check service status
   sudo systemctl status unifi
   ```

2. **Check firewall rules**
   - Verify port 8443 is open
   - Check network path to controller

3. **Restart controller**
   ```bash
   sudo systemctl restart unifi
   ```

#### Issue: Homebridge Not Responding

**Symptoms**:
- HomeKit devices unavailable
- Homebridge UI not accessible

**Diagnosis**:
```bash
# Check if VM is running
ping 10.10.10.50

# Test web UI
curl http://10.10.10.50:8581

# Check from iOS device
# Open Home app and check for accessories
```

**Solutions**:

1. **Restart Homebridge service**
   ```bash
   ssh homebridge@10.10.10.50
   sudo systemctl restart homebridge
   ```

2. **Check logs**
   ```bash
   ssh homebridge@10.10.10.50
   journalctl -u homebridge -f
   ```

3. **Verify network connectivity**
   - Check VLAN configuration
   - Verify mDNS is working

#### Issue: GitHub Actions Workflow Fails

**Symptoms**:
- PR checks fail
- Deployment workflow fails

**Diagnosis**:

1. Check workflow logs in GitHub Actions
2. Look for specific error messages
3. Verify self-hosted runner is online

**Solutions**:

1. **Runner offline**
   ```bash
   # On runner host
   cd actions-runner
   ./run.sh
   ```

2. **Authentication issues**
   - Verify GitHub token is valid
   - Check runner registration

3. **Resource constraints**
   - Check disk space
   - Check memory usage
   - Restart runner if needed

### Network Issues

#### VLAN Misconfiguration

**Symptoms**:
- Devices can't communicate
- WiFi clients can't connect

**Diagnosis**:
```bash
# Check VLAN configuration in UniFi Controller
# Verify switch port profiles
# Check DHCP server status
```

**Solutions**:

1. **Verify VLAN IDs match**
   - Check Terraform configuration
   - Compare with UniFi Controller
   - Apply correct configuration

2. **Check trunk ports**
   - Verify tagged VLANs on switch
   - Ensure native VLAN is correct

#### WiFi Connectivity Issues

**Symptoms**:
- Clients can't connect to WiFi
- Weak signal strength

**Diagnosis**:
- Check AP status in UniFi Controller
- Review RF environment
- Check client connection logs

**Solutions**:

1. **Restart access point**
   - Power cycle AP
   - Or restart from controller

2. **Adjust RF settings**
   - Change channel
   - Adjust transmit power
   - Enable band steering

3. **Check WiFi password**
   - Verify in Terraform configuration
   - Reset if compromised

## Disaster Recovery

### Complete Infrastructure Loss

**Scenario**: Primary site infrastructure is completely unavailable.

#### Recovery Steps

1. **Assess Damage**
   - Identify what's lost
   - Determine recovery priority
   - Document findings

2. **Restore State Files**
   ```bash
   # Restore from backup
   cp backups/terraform.tfstate.backup environments/site-primary/terraform.tfstate
   ```

3. **Verify State Integrity**
   ```bash
   cd environments/site-primary
   terraform state list
   terraform state show <resource>
   ```

4. **Rebuild Infrastructure**
   ```bash
   # If infrastructure is completely new
   terraform apply
   
   # If partially intact
   terraform plan
   # Review carefully before applying
   ```

5. **Verify Services**
   - Test UniFi Controller access
   - Verify network connectivity
   - Test Homebridge functionality
   - Validate automation rules

### State File Corruption

**Scenario**: Terraform state file is corrupted.

#### Recovery Steps

1. **Backup Current State**
   ```bash
   cp terraform.tfstate terraform.tfstate.corrupted
   ```

2. **Restore from Backup**
   ```bash
   cp terraform.tfstate.backup terraform.tfstate
   ```

3. **If No Backup Available**
   ```bash
   # Import existing resources
   terraform import unifi_network.management <network-id>
   terraform import unifi_wlan.main <wlan-id>
   ```

4. **Validate State**
   ```bash
   terraform plan
   # Should show no changes if successful
   ```

### UniFi Controller Failure

**Scenario**: UniFi Controller is down or data is lost.

#### Recovery Steps

1. **Restore Controller Backup**
   - Access controller backup
   - Follow UniFi restore procedures
   - Verify backup is recent

2. **Reconfigure via Terraform**
   ```bash
   cd environments/site-primary
   
   # This will recreate configuration
   terraform apply
   ```

3. **Verify Network Devices**
   - Check device adoption
   - Verify network settings
   - Test connectivity

## Maintenance Tasks

### Weekly Tasks

#### 1. Review Security Alerts

```bash
# Run security scan
tfsec .
checkov -d .

# Review results and address issues
```

#### 2. Check for Terraform Updates

```bash
# Check current version
terraform version

# Check for updates
# Visit: https://www.terraform.io/downloads
```

#### 3. Backup State Files

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup state files
cp environments/*/terraform.tfstate backups/$(date +%Y%m%d)/
```

### Monthly Tasks

#### 1. Review and Update Documentation

- Update runbook with new procedures
- Document any configuration changes
- Update network diagrams if needed

#### 2. Test Disaster Recovery

- Restore from backup in test environment
- Verify recovery procedures work
- Update DR documentation

#### 3. Review Access Controls

- Audit who has repository access
- Review GitHub permissions
- Rotate credentials if needed

#### 4. Update Dependencies

```bash
# Update provider versions
terraform init -upgrade

# Test updated providers
terraform plan
```

### Quarterly Tasks

#### 1. Full Security Audit

- Review all firewall rules
- Audit network access
- Test security controls
- Penetration testing (if applicable)

#### 2. Capacity Planning

- Review network utilization
- Plan for expansion
- Budget for new equipment

#### 3. Disaster Recovery Drill

- Full DR exercise
- Document findings
- Update procedures

## Emergency Procedures

### Security Incident

#### Suspected Breach

1. **Isolate Affected Systems**
   ```bash
   # Disable affected VLANs or ports
   # In UniFi Controller or via emergency Terraform apply
   ```

2. **Review Logs**
   - UniFi Controller logs
   - Firewall logs
   - Authentication logs

3. **Assess Impact**
   - Identify compromised systems
   - Determine data exposure
   - Document findings

4. **Remediate**
   - Change all passwords
   - Update firewall rules
   - Apply security patches

5. **Post-Incident Review**
   - Document incident
   - Update security procedures
   - Implement preventive measures

### Network Outage

#### Complete Network Down

1. **Check Physical Layer**
   - Verify power to equipment
   - Check cable connections
   - Test with known-good devices

2. **Check Gateway/Router**
   - Reboot if necessary
   - Verify WAN connectivity
   - Check ISP status

3. **Check Controller**
   - Verify controller is accessible
   - Check device adoption status
   - Review recent changes

4. **Restore Service**
   - Apply last-known-good configuration
   - Reboot devices systematically
   - Test connectivity

### Data Loss

#### State File Lost

Follow [State File Corruption](#state-file-corruption) procedures.

#### Configuration Lost

1. **Check Git History**
   ```bash
   git log --all -- environments/site-primary/
   git checkout <commit-hash> -- environments/site-primary/
   ```

2. **Restore from Backup**
   - Use local backups if available
   - Clone fresh from GitHub

3. **Rebuild Configuration**
   - Document current infrastructure
   - Recreate Terraform configuration
   - Import existing resources

## Appendix

### Useful Commands

#### Terraform

```bash
# Initialize
terraform init

# Plan changes
terraform plan

# Apply changes
terraform apply

# Destroy resources
terraform destroy

# Show current state
terraform show

# List resources
terraform state list

# Import existing resource
terraform import <resource_type>.<name> <id>
```

#### Git

```bash
# Check status
git status

# View history
git log --oneline

# Create branch
git checkout -b branch-name

# Undo local changes
git checkout -- file.tf

# Reset to commit
git reset --hard <commit-hash>
```

#### GitHub CLI

```bash
# List pull requests
gh pr list

# Create pull request
gh pr create

# View workflow runs
gh run list

# Trigger workflow
gh workflow run terraform-apply.yml
```

### Contact Information

**Emergency Contacts**:
- Primary: [Add contact]
- Secondary: [Add contact]
- On-Call: [Add schedule/contact]

**Vendor Support**:
- Ubiquiti Support: https://help.ui.com/
- GitHub Support: https://support.github.com/

### Change Log

| Date       | Change                          | Author        |
|------------|---------------------------------|---------------|
| 2024-12-14 | Initial runbook creation        | System        |

---

**Last Updated**: 2024-12-14
**Next Review**: 2025-01-14
