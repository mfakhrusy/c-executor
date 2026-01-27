# Lightweight C Code Executor

A minimal, self-hosted C code execution API using Python's built-in HTTP server and gcc.

## Requirements

- Python 3.6+
- GCC compiler
- Linux (uses resource limits)

## Quick Start (Local Testing)

```bash
# Install gcc if not present
sudo apt update && sudo apt install -y gcc

# Run the server
cd ~/c-executor
python3 server.py
```

Server runs on `http://127.0.0.1:3001`

## Production Deployment on VPS

### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install gcc and python3
sudo apt install -y gcc python3
```

### Step 2: Copy Files to Server

```bash
# From your local machine
scp -r ~/c-executor user@your-server:/tmp/

# On the server
sudo mkdir -p /var/www/c-executor
sudo cp /tmp/c-executor/* /var/www/c-executor/
sudo chown -R nobody:nogroup /var/www/c-executor
sudo chmod +x /var/www/c-executor/server.py
```

### Step 3: Install Systemd Service

```bash
# Copy service file
sudo cp /var/www/c-executor/c-executor.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable c-executor
sudo systemctl start c-executor

# Check status
sudo systemctl status c-executor

# View logs
sudo journalctl -u c-executor -f
```

### Step 4: Configure Caddy Reverse Proxy

Add to your `/etc/caddy/Caddyfile`:

```
c-playground.your.domain {
    # Serve static files (the playground HTML)
    root * /var/www/c-executor
    file_server

    # Reverse proxy API requests to the Python server
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

### Step 5: Test

Open `https://c-playground.your.domain` in your browser.

Or test the API directly:

```bash
curl -X POST https://c-playground.your.domain/api/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "#include<stdio.h>\nint main() { printf(\"Hello\"); return 0; }"}'
```

## API Reference

### POST /execute

Execute C code.

**Request:**
```json
{
  "code": "#include<stdio.h>\nint main() { printf(\"Hello\"); return 0; }"
}
```

**Response (success):**
```json
{
  "success": true,
  "stage": "run",
  "stdout": "Hello",
  "stderr": "",
  "exit_code": 0
}
```

**Response (compile error):**
```json
{
  "success": false,
  "stage": "compile",
  "stdout": "",
  "stderr": "main.c:1:1: error: ...",
  "exit_code": 1
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Embedding in Your Blog (iframe)

Add this to your blog post HTML:

```html
<iframe 
  src="https://c-playground.your.domain" 
  width="100%" 
  height="600" 
  frameborder="0"
  style="border: 1px solid #333; border-radius: 8px;"
></iframe>
```

Or embed just a specific example by creating a custom HTML file with pre-filled code.

## Security Considerations

⚠️ **This executes arbitrary code on your server!**

The following protections are in place:

1. **Resource limits** - Memory (128MB), CPU time (5s), file size (1MB)
2. **Timeouts** - Compile (10s) and execution (5s) timeouts
3. **Systemd hardening** - Runs as `nobody`, limited filesystem access
4. **Output limits** - Max 64KB output to prevent DoS

### Additional Hardening (Recommended)

1. **Run in a container:**
   ```bash
   # Create a simple Dockerfile
   docker run --rm -it --memory=256m --cpus=0.5 \
     -v /var/www/c-executor:/app -p 3001:3001 \
     python:3.11-slim python3 /app/server.py
   ```

2. **Use a firewall:**
   ```bash
   sudo ufw allow from 127.0.0.1 to any port 3001
   ```

3. **Rate limiting in Caddy:**
   ```
   c-playground.your.domain {
       rate_limit {
           zone dynamic_zone {
               key {remote_host}
               events 10
               window 1m
           }
       }
       # ... rest of config
   }
   ```

## Troubleshooting

### "gcc: command not found"

```bash
sudo apt install -y gcc build-essential
```

### "Permission denied" when running binary

The `nobody` user can't execute in certain directories. Ensure `/tmp` is executable:

```bash
mount | grep tmp
# Should NOT have noexec
```

### Service won't start

Check logs:
```bash
sudo journalctl -u c-executor -n 50
```

### API returns connection error

1. Check if service is running: `sudo systemctl status c-executor`
2. Check if port is listening: `ss -tlnp | grep 3001`
3. Check Caddy config: `sudo caddy validate --config /etc/caddy/Caddyfile`

## Memory Usage

Typical memory footprint:
- Python server: ~20-30MB
- Per compilation: ~50-100MB (temporary)

Total: **~50-100MB** typical, **~200MB** peak

This should run fine on a 1GB Linode.
