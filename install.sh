#!/bin/bash
#
# C Executor Installation Script
# Run this on your VPS as root
#
set -e

echo "=== C Executor Installation ==="
echo ""

# Step 1: Install base dependencies
echo "[1/6] Installing base dependencies..."
apt update
apt install -y gcc python3 software-properties-common bubblewrap

# Step 2: Verify bubblewrap
echo "[2/6] Verifying bubblewrap..."
if ! command -v bwrap &> /dev/null; then
    echo "ERROR: bubblewrap installation failed"
    exit 1
fi
bwrap --version | head -1

# Step 3: Create user and directories
echo "[3/6] Creating c-executor user..."
if ! id -u c-executor &>/dev/null; then
    useradd -r -s /usr/sbin/nologin -d /var/www/c-executor c-executor
    echo "Created c-executor user"
fi

mkdir -p /var/www/c-executor

# Step 4: Copy project files
echo "[4/6] Copying project files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/index.html" /var/www/c-executor/ 2>/dev/null || true
cp "$SCRIPT_DIR/server.py" /var/www/c-executor/
cp "$SCRIPT_DIR/c-executor.service" /var/www/c-executor/
cp "$SCRIPT_DIR/README.md" /var/www/c-executor/ 2>/dev/null || true
cp "$SCRIPT_DIR/INSTALL.md" /var/www/c-executor/ 2>/dev/null || true

# Step 5: Set permissions
echo "[5/6] Setting permissions..."
chown -R c-executor:c-executor /var/www/c-executor
chmod +x /var/www/c-executor/server.py

# Step 6: Install systemd service
echo "[6/6] Installing systemd service..."
if [ -f /var/www/c-executor/c-executor.service ]; then
    cp /var/www/c-executor/c-executor.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable c-executor
    systemctl start c-executor
    echo "Service installed and started."
else
    echo "ERROR: c-executor.service not found in /var/www/c-executor/"
    echo "Make sure c-executor.service exists in the same directory as install.sh"
    exit 1
fi

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Files copied to /var/www/c-executor/"
echo ""
echo "Service status:"
systemctl status c-executor --no-pager 2>/dev/null || true
echo ""
echo "Next steps:"
echo "  1. Add Caddy config (see INSTALL.md)"
echo "  2. Reload Caddy: sudo systemctl reload caddy"
echo "  3. Open https://c-playground.your-domain.com"
