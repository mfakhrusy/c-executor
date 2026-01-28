# TODO: outdated, using bubblewrap now
# C Executor Installation Guide

A sandboxed C code execution API using Python + gcc + firejail.

## Prerequisites

- Ubuntu/Debian VPS (20.04+)
- Caddy web server installed
- Root access

---

## Section 1: Install Dependencies

```bash
sudo apt update && sudo apt install -y gcc python3 software-properties-common
```

---

## Section 2: Install Firejail (PPA)

```bash
sudo add-apt-repository ppa:deki/firejail
sudo apt-get update
sudo apt-get install -y firejail firejail-profiles
```

---

## Section 3: Verify Firejail

```bash
firejail --version
```

Expected output: `firejail version 0.9.x or higher`

---

## Section 4: Create Directory

```bash
sudo mkdir -p /var/www/c-executor
```

---

## Section 5: Copy Files to Server

Run this **from your local machine**:

```bash
scp ~/c-executor/server.py root@YOUR_SERVER:/var/www/c-executor/
scp ~/c-executor/index.html root@YOUR_SERVER:/var/www/c-executor/
scp ~/c-executor/c-executor.service root@YOUR_SERVER:/var/www/c-executor/
```

---

## Section 6: Set Permissions

```bash
sudo chown -R c-executor:c-executor /var/www/c-executor
sudo chmod +x /var/www/c-executor/server.py
```

---

## Section 7: Install Systemd Service

```bash
sudo cp /var/www/c-executor/c-executor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable c-executor
sudo systemctl start c-executor
```

---

## Section 8: Check Service Status

```bash
sudo systemctl status c-executor
```

Expected output:
```
● c-executor.service - C Code Executor API
     Loaded: loaded
     Active: active (running)
```

---

## Section 9: Test API Locally on Server

```bash
curl -X POST http://127.0.0.1:3001/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "#include<stdio.h>\nint main() { printf(\"Hello\"); return 0; }"}'
```

Expected output:
```json
{"success": true, "stage": "run", "stdout": "Hello", "stderr": "", "exit_code": 0}
```

---

## Section 10: Configure Caddy

Edit your Caddyfile:

```bash
sudo vim /etc/caddy/Caddyfile
```

Add this block:

```
c-playground.your.domain {
    root * /var/www/c-executor
    file_server

    handle /api/* {
        uri strip_prefix /api
        reverse_proxy 127.0.0.1:3001
    }
}
```

---

## Section 11: Reload Caddy

```bash
sudo systemctl reload caddy
```

---

## Section 12: Test Production

Open in browser:
```
https://c-playground.your.domain
```

Or test API:
```bash
curl -X POST https://c-playground.your.domain/api/execute \
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

### Test firejail manually

```bash
echo '#include<stdio.h>
int main() { printf("test"); return 0; }' > /tmp/test.c
gcc -o /tmp/test /tmp/test.c
firejail --quiet --net=none --seccomp /tmp/test
```

### Firejail permission issues

If firejail fails with permission errors:

```bash
sudo chmod 4755 /usr/bin/firejail
```

---

## Security Features

| Feature | Protection |
|---------|------------|
| `--seccomp` | Syscall filtering |
| `--net=none` | No network access |
| `--private=DIR` | Isolated filesystem |
| `--private-dev` | Limited /dev access |
| `--caps.drop=all` | No Linux capabilities |
| `--noroot` | No root in sandbox |
| `--nonewprivs` | Can't gain privileges |
| `--rlimit-*` | Resource limits |
| PIE/RELRO | ASLR + memory protection |

---

## Embed in Blog (iframe)

```html
<iframe 
  src="https://c-playground.your.domain" 
  width="100%" 
  height="600" 
  frameborder="0"
  style="border: 1px solid #333; border-radius: 8px;">
</iframe>
```

---

## Restrict CORS (Production)

To allow only your blog domain, set environment variable in the service file:

```bash
sudo nano /etc/systemd/system/c-executor.service
```

Add under `[Service]`:

```
Environment=ALLOWED_ORIGINS=https://blog.your.domain,https://c-playground.your.domain
```

Then reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart c-executor
```
