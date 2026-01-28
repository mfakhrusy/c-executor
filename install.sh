#!/bin/bash
set -e

echo "Installing C Executor..."

# Install dependencies
apt update
apt install -y gcc bubblewrap python3

# Create dedicated user (if not exists)
if ! id -u c-executor &>/dev/null; then
    useradd -r -s /usr/sbin/nologin c-executor
    echo "Created user: c-executor"
fi

# Enable unprivileged user namespaces (required for bwrap)
sysctl -w kernel.unprivileged_userns_clone=1
echo 'kernel.unprivileged_userns_clone=1' > /etc/sysctl.d/99-userns.conf

# Setup application directory
mkdir -p /var/www/c-executor
cp server.py /var/www/c-executor/
chown -R c-executor:c-executor /var/www/c-executor

# Install and start service
cp c-executor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable c-executor
systemctl restart c-executor

echo ""
echo "Done! Service status:"
systemctl status c-executor --no-pager

echo ""
echo "Test with:"
echo 'curl -X POST http://localhost:3001/execute -H "Content-Type: application/json" -d '"'"'{"code": "#include <stdio.h>\nint main() { printf(\"Hello\"); return 0; }"}'"'"
