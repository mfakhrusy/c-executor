#!/bin/bash
set -e

apt update
apt install -y gcc bubblewrap python3

mkdir -p /var/www/c-executor
cp server.py /var/www/c-executor/
cp c-executor.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable c-executor
systemctl restart c-executor

echo "Done. Test with:"
echo 'curl -X POST http://localhost:3001/execute -H "Content-Type: application/json" -d '"'"'{"code": "#include <stdio.h>\nint main() { printf(\"Hello\"); return 0; }"}'"'"
