# Network Design Documentation

## Overview

This document describes the network architecture and design for the Boycivenga multi-site home network lab managed through Terraform.

## Network Topology

### Site-Primary Network Architecture

```
Internet
   │
   ├─► USG/UDM (UniFi Gateway)
   │
   ├─► Management Network (VLAN 10)
   │   ├─ 10.10.10.0/24
   │   ├─ DHCP Range: 10.10.10.100-254
   │   ├─ Gateway: 10.10.10.1
   │   └─ Purpose: Network equipment, servers, management devices
   │
   ├─► IoT Network (VLAN 20)
   │   ├─ 10.10.20.0/24
   │   ├─ DHCP Range: 10.10.20.100-254
   │   ├─ Gateway: 10.10.20.1
   │   └─ Purpose: Smart home devices, IoT sensors
   │
   └─► Guest Network (VLAN 30)
       ├─ 10.10.30.0/24
       ├─ DHCP Range: 10.10.30.100-254
       ├─ Gateway: 10.10.30.1
       └─ Purpose: Guest WiFi, isolated from main network
```

### Site-Secondary Network Architecture

```
Internet
   │
   ├─► USG/UDM (UniFi Gateway)
   │
   ├─► Management Network (VLAN 10)
   │   ├─ 10.20.10.0/24
   │   ├─ DHCP Range: 10.20.10.100-254
   │   ├─ Gateway: 10.20.10.1
   │   └─ Purpose: Network equipment, management devices
   │
   └─► IoT Network (VLAN 20)
       ├─ 10.20.20.0/24
       ├─ DHCP Range: 10.20.20.100-254
       ├─ Gateway: 10.20.20.1
       └─ Purpose: Smart home devices, IoT sensors
```

## VLAN Design

### VLAN Strategy

| VLAN ID | Name       | Purpose                    | Subnet         | Notes                          |
|---------|------------|----------------------------|----------------|--------------------------------|
| 10      | Management | Network infrastructure     | x.x.10.0/24    | Trusted devices only           |
| 20      | IoT        | Smart home devices         | x.x.20.0/24    | Isolated from management       |
| 30      | Guest      | Guest WiFi access          | x.x.30.0/24    | Internet-only, isolated        |

### VLAN Segmentation Benefits

1. **Security**: Isolate untrusted devices from critical infrastructure
2. **Performance**: Reduce broadcast domains
3. **Management**: Organize devices by function
4. **QoS**: Apply quality of service policies per VLAN

## IP Address Allocation

### Site-Primary (10.10.0.0/16)

#### Management VLAN (10.10.10.0/24)

| Range             | Purpose                  | Assignment Type |
|-------------------|--------------------------|-----------------|
| 10.10.10.1        | Gateway                  | Static          |
| 10.10.10.2-10     | Network equipment        | Static          |
| 10.10.10.11-50    | Servers & VMs            | Static          |
| 10.10.10.51-99    | Reserved                 | Static          |
| 10.10.10.100-254  | DHCP pool                | Dynamic         |

**Notable Assignments**:
- 10.10.10.1: USG/UDM Gateway
- 10.10.10.2: Primary switch
- 10.10.10.10: UniFi Controller
- 10.10.10.50: Homebridge VM

#### IoT VLAN (10.10.20.0/24)

| Range             | Purpose                  | Assignment Type |
|-------------------|--------------------------|-----------------|
| 10.10.20.1        | Gateway                  | Static          |
| 10.10.20.2-99     | Static IoT devices       | Static          |
| 10.10.20.100-254  | DHCP pool                | Dynamic         |

#### Guest VLAN (10.10.30.0/24)

| Range             | Purpose                  | Assignment Type |
|-------------------|--------------------------|-----------------|
| 10.10.30.1        | Gateway                  | Static          |
| 10.10.30.100-254  | DHCP pool                | Dynamic         |

### Site-Secondary (10.20.0.0/16)

Similar structure to Site-Primary, using 10.20.x.x addressing to avoid conflicts.

## Firewall Rules

### Default Policy

- **Management → All**: Allow (trusted network)
- **IoT → Management**: Deny (security)
- **IoT → Internet**: Allow (required functionality)
- **Guest → All**: Deny (isolated)
- **Guest → Internet**: Allow (guest access)

### Specific Rules

#### Rule 1: Block IoT to Management

```hcl
{
  name             = "Block IoT to Management"
  action           = "drop"
  protocol         = "all"
  src_network_type = "ADDRv4"
  dst_network_type = "ADDRv4"
  enabled          = true
  rule_index       = 2000
}
```

**Purpose**: Prevent compromised IoT devices from accessing management network.

#### Rule 2: Allow Management to All

```hcl
{
  name             = "Allow Management to All"
  action           = "accept"
  protocol         = "all"
  src_network_type = "ADDRv4"
  dst_network_type = "ADDRv4"
  enabled          = true
  rule_index       = 1000
}
```

**Purpose**: Allow administrators full access for troubleshooting and management.

#### Rule 3: Block Guest to Private Networks

```hcl
{
  name             = "Block Guest to Private"
  action           = "drop"
  protocol         = "all"
  src_network_type = "ADDRv4"
  dst_network_type = "ADDRv4"
  enabled          = true
  rule_index       = 2100
}
```

**Purpose**: Ensure guest network is completely isolated.

### mDNS/Bonjour Considerations

For HomeKit and other mDNS services to work across VLANs:

1. Enable mDNS reflector on USG/UDM
2. Allow UDP port 5353 between specific VLANs
3. Configure Homebridge on Management VLAN with access to IoT VLAN

## Wireless Networks (WLANs)

### Site-Primary

| SSID             | Security | VLAN | Band  | Purpose             |
|------------------|----------|------|-------|---------------------|
| Home-WiFi        | WPA3/2   | 10   | Both  | Primary WiFi        |
| Guest-WiFi       | WPA2     | 30   | Both  | Guest access        |

### Site-Secondary

| SSID                 | Security | VLAN | Band  | Purpose             |
|----------------------|----------|------|-------|---------------------|
| Home-WiFi-Secondary  | WPA3/2   | 10   | Both  | Primary WiFi        |

### WiFi Best Practices

1. **Security**: Use WPA3 where supported, WPA2 minimum
2. **Band Steering**: Enable to prefer 5GHz
3. **Fast Roaming**: Enable 802.11r for seamless handoff
4. **Guest Isolation**: Enable client isolation on guest networks
5. **Hidden SSIDs**: Consider for security-sensitive networks

## Switch Port Profiles

### Profile: Access-Point

**Purpose**: Trunk port for UniFi Access Points

**Configuration**:
- Native VLAN: 10 (Management)
- Tagged VLANs: 20 (IoT), 30 (Guest)
- PoE Mode: Auto

**Use Case**: Access points need access to multiple VLANs to broadcast different SSIDs.

### Profile: IoT-Device

**Purpose**: Access port for IoT devices requiring wired connection

**Configuration**:
- Native VLAN: 20 (IoT)
- PoE Mode: Auto

**Use Case**: Cameras, smart hubs, and other IoT devices requiring Ethernet.

### Profile: Management-Device

**Purpose**: Access port for trusted management devices

**Configuration**:
- Native VLAN: 10 (Management)
- PoE Mode: Auto (if needed)

**Use Case**: Servers, NAS, management workstations.

## DNS Configuration

### Internal DNS

**Primary DNS**: 10.10.10.1 (Gateway)
**Secondary DNS**: 8.8.8.8 (Google Public DNS)

### Domain Names

- Management: `mgmt.local`
- IoT: `iot.local`

### DNS-Based Filtering

Consider implementing:
- Pi-hole for ad blocking
- DNS-based content filtering
- Local DNS records for services

## DHCP Configuration

### DHCP Server

- **Location**: Running on USG/UDM per VLAN
- **Lease Time**: 24 hours (adjustable)
- **Reservations**: Use for devices requiring consistent IPs

### DHCP Options

**Option 6 (DNS Servers)**:
- Primary: Gateway IP
- Secondary: 8.8.8.8

**Option 3 (Default Gateway)**:
- Respective VLAN gateway

**Option 15 (Domain Name)**:
- Per-VLAN domain names

## Network Services

### Services on Management VLAN

| Service             | IP              | Port(s)  | Purpose                    |
|---------------------|-----------------|----------|----------------------------|
| UniFi Controller    | 10.10.10.10     | 8443     | Network management         |
| Homebridge          | 10.10.10.50     | 8581     | HomeKit bridge UI          |
| Homebridge          | 10.10.10.50     | 51826    | HomeKit protocol           |
| Home Assistant      | 10.10.10.51     | 8123     | Smart home automation      |

### Port Forwarding

**Principle**: Avoid port forwarding where possible. Use VPN for remote access.

If required:
- Change default ports
- Implement rate limiting
- Use strong authentication
- Consider Cloudflare Tunnel or similar

## Quality of Service (QoS)

### Priority Levels

1. **High**: VoIP, video conferencing
2. **Medium**: General internet, streaming
3. **Low**: Background downloads, updates

### Per-VLAN QoS

- **Management**: High priority for management traffic
- **IoT**: Medium priority
- **Guest**: Low priority

## Security Considerations

### Network Segmentation

- **Defense in Depth**: Multiple layers of security
- **Least Privilege**: Only allow necessary access
- **Isolation**: Untrusted devices on separate VLANs

### Firewall Best Practices

1. Default deny policy
2. Explicit allow rules
3. Regular review and cleanup
4. Logging enabled for denied traffic

### IoT Security

1. **Isolation**: IoT VLAN separate from management
2. **Egress Filtering**: Block IoT from initiating connections to management
3. **Monitoring**: Log and monitor IoT traffic
4. **Updates**: Keep IoT firmware updated

### Guest Network Security

1. **Complete Isolation**: No access to internal networks
2. **Client Isolation**: Guests can't see each other
3. **Bandwidth Limiting**: Prevent abuse
4. **Captive Portal**: Optional terms of service

## Monitoring and Troubleshooting

### UniFi Network Monitoring

- Device health
- Traffic statistics
- Client connections
- Interference detection

### Key Metrics

- **Bandwidth utilization**
- **Device uptime**
- **WiFi channel utilization**
- **Client count per AP**

### Troubleshooting Tools

1. **Ping**: Basic connectivity
2. **Traceroute**: Path diagnostics
3. **UniFi Tools**: Built-in diagnostics
4. **Packet Capture**: Deep analysis

## Expansion Planning

### Adding New VLANs

1. Plan IP addressing
2. Define firewall rules
3. Update Terraform configuration
4. Test thoroughly before production

### Scaling Considerations

- **IP Space**: /24 networks support 254 hosts
- **Broadcast Domains**: Consider /23 or /22 for large networks
- **Access Points**: Plan for capacity and coverage
- **Switches**: Ensure adequate port density

## Site-to-Site Connectivity

### Future Consideration

For connecting multiple sites:

1. **VPN Tunnel**: IPsec site-to-site VPN
2. **Addressing**: Ensure no IP conflicts
3. **Routing**: Dynamic routing or static routes
4. **Firewall**: Rules for inter-site traffic

### Example VPN Configuration

```
Site-Primary (10.10.0.0/16)
        │
        │ IPsec VPN
        │
Site-Secondary (10.20.0.0/16)
```

## Network Diagram

### Physical Layout (Site-Primary)

```
[Internet] ──► [USG/UDM]
                   │
                   ├──► [Switch] ─┬─► [Access Point 1]
                   │              ├─► [Access Point 2]
                   │              ├─► [Homebridge VM]
                   │              ├─► [Server/NAS]
                   │              └─► [IoT Hub]
                   │
                   └──► [Devices on WiFi]
                          ├─► Phones, Laptops (Management VLAN)
                          ├─► Smart Devices (IoT VLAN)
                          └─► Guest Devices (Guest VLAN)
```

## References

- [UniFi Documentation](https://help.ui.com/)
- [VLAN Best Practices](https://www.cisco.com/c/en/us/support/docs/lan-switching/vlan/10023-2.html)
- [Home Network Design](https://www.reddit.com/r/homelab/)

## Changelog

### 2024-12-14

- Initial network design documentation
- Defined VLAN structure for multi-site
- Documented firewall rules and security policies

---

For questions or suggestions, see [CONTRIBUTING.md](../CONTRIBUTING.md).
