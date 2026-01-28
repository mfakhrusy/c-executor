#!/bin/bash
set -e

echo "=== C Executor Installation ==="

# Install deps
apt update
apt install -y gcc python3 bubblewrap

# Setup directory
mkdir -p /var/www/c-executor

# Copy files (run from same dir as script)
cp "$(dirname "$0")/server.py" /var/www/c-executor/
cp "$(dirname "$0")/c-executor.service" /etc/systemd/system/

systemctl daemon-reload
systemctl enable c-executor
systemctl restart c-executor

echo "Done! Check status: sudo systemctl status c-executor"
