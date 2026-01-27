#!/bin/bash
#
# C Executor Installation Script
# Run this on your VPS as root
#
set -e

echo "=== C Executor Installation ==="
echo ""

# Step 1: Install dependencies
echo "[1/5] Installing dependencies..."
apt update
apt install -y gcc python3

# Step 2: Create directory and copy files
echo "[2/5] Setting up files..."
mkdir -p /var/www/c-executor

# Step 3: Install systemd service
echo "[3/5] Installing systemd service..."
cp /var/www/c-executor/c-executor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable c-executor
systemctl start c-executor

# Step 4: Check status
echo "[4/5] Checking service status..."
systemctl status c-executor --no-pager

# Step 5: Done
echo ""
echo "[5/5] Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Add Caddy config (see INSTALL.md)"
echo "  2. Reload Caddy: sudo systemctl reload caddy"
echo "  3. Open https://c-playground.your-domain.com"
