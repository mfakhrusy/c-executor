# C Executor Installation Guide

A sandboxed C code execution API using Python + GCC + bubblewrap.

## Prerequisites

- Ubuntu/Debian VPS (20.04+)
- Root access
- A domain pointed to your server (for HTTPS)

---

## Option 1: Quick Install

```bash
git clone https://github.com/mfakhrusy/c-playground-wasmer.git
cd c-playground-wasmer
sudo bash install.sh
```

This installs:
- GCC, Python3, bubblewrap, curl
- Caddy web server
- Copies files to `/var/www/c-executor`
- Sets up systemd service

**Note:** You'll need to manually configure Caddy for your domain (see Section 6).

---

## Option 2: Manual Installation

### Section 1: Install Dependencies

```bash
sudo apt update
sudo apt install -y gcc python3 bubblewrap curl
```

---

### Section 2: Install Caddy

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

---

### Section 3: Verify Bubblewrap

```bash
bwrap --version
```

Expected output: `bubblewrap 0.x.x`

---

### Section 4: Create Directory and Copy Files

```bash
sudo mkdir -p /var/www/c-executor
sudo cp server.py index.html /var/www/c-executor/
sudo cp c-executor.service /etc/systemd/system/
```

---

### Section 5: Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable c-executor
sudo systemctl start c-executor
```

Check status:

```bash
sudo systemctl status c-executor
```

---

### Section 6: Configure Caddy

Edit your Caddyfile:

```bash
sudo nano /etc/caddy/Caddyfile
```

Add this block (replace `c-executor.yourdomain.com` with your domain):

```
c-executor.yourdomain.com {
    root * /var/www/c-executor
    file_server

    handle /api/* {
        uri strip_prefix /api
        reverse_proxy 127.0.0.1:3001
    }
}
```

Reload Caddy:

```bash
sudo systemctl reload caddy
```

---

### Section 7: Test

Test API locally:

```bash
curl -X POST http://127.0.0.1:3001/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "#include<stdio.h>\nint main() { printf(\"Hello\"); return 0; }"}'
```

Expected output:
```json
{"success": true, "stage": "run", "stdout": "Hello", "stderr": "", "exit_code": 0}
```

Test production:

```bash
curl -X POST https://c-executor.yourdomain.com/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "#include<stdio.h>\nint main() { printf(\"Hello\"); return 0; }"}'
```

---

## Troubleshooting

### View logs

```bash
sudo journalctl -u c-executor -f
```

### Restart service

```bash
sudo systemctl restart c-executor
```

### Check port

```bash
ss -tlnp | grep 3001
```

### Test bubblewrap manually

```bash
echo '#include<stdio.h>
int main() { printf("test"); return 0; }' > /tmp/test.c
bwrap --ro-bind / / --dev /dev /usr/bin/gcc -o /tmp/test /tmp/test.c
/tmp/test
```

---

## Security Features

| Feature | Description |
|---------|-------------|
| `--tmpfs /` | Temporary root filesystem |
| `--ro-bind` | Read-only system directories |
| `--unshare-pid` | Isolated PID namespace |
| `--die-with-parent` | Process dies with server |
| Timeouts | 10s compile, 5s run |
| Output limits | 10KB max stdout/stderr |

---

## Embed in Blog (iframe)

```html
<iframe 
  src="https://c-executor.yourdomain.com" 
  width="100%" 
  height="600" 
  frameborder="0"
  style="border: 1px solid #333; border-radius: 8px;">
</iframe>
```
