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

# Step 3: Configure firejail
echo "[3/7] Configuring firejail..."
firejail --version

# Create dedicated c-executor user (firejail blocks 'nobody' user)
if ! id -u c-executor &>/dev/null; then
    useradd -r -s /usr/sbin/nologin -d /var/www/c-executor c-executor
    echo "Created c-executor user"
fi

# Allow c-executor user to use firejail
if [ -f /etc/firejail/firejail.users ]; then
    if ! grep -q "^c-executor$" /etc/firejail/firejail.users; then
        echo "c-executor" >> /etc/firejail/firejail.users
        echo "Added c-executor to firejail.users"
    fi
else
    echo "c-executor" > /etc/firejail/firejail.users
    echo "Created firejail.users with c-executor"
fi

# Fix firejail permissions
mkdir -p /run/firejail
chmod 755 /run/firejail
chown root:root /run/firejail
chmod 4755 /usr/bin/firejail

# Step 4: Copy project files
echo "[4/7] Copying project files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p /var/www/c-executor
cp "$SCRIPT_DIR/index.html" /var/www/c-executor/
cp "$SCRIPT_DIR/server.py" /var/www/c-executor/
cp "$SCRIPT_DIR/c-executor.service" /var/www/c-executor/
cp "$SCRIPT_DIR/README.md" /var/www/c-executor/ 2>/dev/null || true
cp "$SCRIPT_DIR/INSTALL.md" /var/www/c-executor/ 2>/dev/null || true

# Step 5: Set permissions
echo "[5/7] Setting permissions..."
chown -R c-executor:c-executor /var/www/c-executor
chmod +x /var/www/c-executor/server.py

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
echo "Files copied to /var/www/c-executor/"
echo ""
echo "Next steps:"
echo "  1. Add Caddy config (see INSTALL.md)"
echo "  2. Reload Caddy: sudo systemctl reload caddy"
echo "  3. Open https://c-playground.your-domain.com"
