#!/bin/bash
set -e

echo "=== C Executor Installation ==="

SCRIPT_DIR="$(dirname "$0")"

# Install deps
apt update
apt install -y gcc python3 bubblewrap curl

# Install Caddy
if ! command -v caddy &> /dev/null; then
    echo "Installing Caddy..."
    apt install -y debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
    apt update
    apt install -y caddy
fi

# Setup directory
mkdir -p /var/www/c-executor

# Copy files
cp "$SCRIPT_DIR/server.py" /var/www/c-executor/
cp "$SCRIPT_DIR/index.html" /var/www/c-executor/
cp "$SCRIPT_DIR/c-executor.service" /etc/systemd/system/

# Configure Caddy -- TODO
# cat > /etc/caddy/Caddyfile << 'EOF'
# :80 {
#     root * /var/www/c-executor
#     file_server

#     handle /api/execute {
#         reverse_proxy localhost:3001
#     }
# }
# EOF

# Start services
systemctl daemon-reload
systemctl enable c-executor caddy
systemctl restart c-executor
systemctl restart caddy

echo "Done!"
echo "  Backend: sudo systemctl status c-executor"
echo "  Frontend: sudo systemctl status caddy"
echo "  Open: http://localhost"
