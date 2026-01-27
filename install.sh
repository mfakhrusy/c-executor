#!/bin/bash
#
# C Executor Installation Script
# Run this on your VPS as root
#
set -e

echo "=== C Executor Installation ==="
echo ""

# Step 1: Install base dependencies
echo "[1/7] Installing base dependencies..."
apt update

# skip python if you have it (or run through uv)
apt install -y gcc python3 software-properties-common

# Step 2: Install firejail from PPA
echo "[2/7] Installing firejail from PPA..."
add-apt-repository -y ppa:deki/firejail
apt-get update
apt-get install -y firejail firejail-profiles

# Step 3: Verify firejail
echo "[3/7] Verifying firejail installation..."
firejail --version

# Step 4: Create directory
echo "[4/7] Setting up directory..."
mkdir -p /var/www/c-executor

# Step 5: Set permissions
echo "[5/7] Setting permissions..."
chown -R nobody:nogroup /var/www/c-executor
chmod +x /var/www/c-executor/server.py 2>/dev/null || true

# Step 6: Install systemd service
echo "[6/7] Installing systemd service..."
if [ -f /var/www/c-executor/c-executor.service ]; then
    cp /var/www/c-executor/c-executor.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable c-executor
    systemctl start c-executor
    echo "Service installed and started."
else
    echo "Warning: c-executor.service not found. Copy files first, then run:"
    echo "  cp /var/www/c-executor/c-executor.service /etc/systemd/system/"
    echo "  systemctl daemon-reload && systemctl enable --now c-executor"
fi

# Step 7: Check status
echo "[7/7] Checking service status..."
systemctl status c-executor --no-pager || true

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Next steps:"
echo "  1. Copy files to /var/www/c-executor/ (if not already done)"
echo "  2. Add Caddy config (see INSTALL.md)"
echo "  3. Reload Caddy: sudo systemctl reload caddy"
echo "  4. Open https://c-playground.your-domain.com"
