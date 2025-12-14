#!/bin/bash
set -e

echo "Setting up Homebridge..."

# Update system
apt-get update
apt-get upgrade -y

# Install Node.js (required for Homebridge)
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt-get install -y nodejs

# Install Homebridge
npm install -g --unsafe-perm homebridge homebridge-config-ui-x

# Install plugins
%{ for plugin in homebridge_plugins ~}
npm install -g ${plugin}
%{ endfor ~}

# Create homebridge user
useradd -m -s /bin/bash homebridge || true

# Create config directory
mkdir -p /var/lib/homebridge
chown -R homebridge:homebridge /var/lib/homebridge

# Write Homebridge configuration
cat > /var/lib/homebridge/config.json <<'EOF'
${homebridge_config}
EOF

chown homebridge:homebridge /var/lib/homebridge/config.json

# Create systemd service
cat > /etc/systemd/system/homebridge.service <<'EOF'
[Unit]
Description=Homebridge
After=network.target

[Service]
Type=simple
User=homebridge
ExecStart=/usr/bin/homebridge -I
Restart=always
RestartSec=10
StandardOutput=append:/var/log/homebridge.log
StandardError=append:/var/log/homebridge.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable homebridge
systemctl start homebridge

echo "Homebridge setup complete!"
echo "Access the UI at: http://$(hostname -I | awk '{print $1}'):8581"
