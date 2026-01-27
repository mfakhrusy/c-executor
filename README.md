# Lightweight C Code Executor

A sandboxed C code execution API using Python + gcc + firejail.

## Features

- **Firejail sandbox** - Both compilation and execution run in isolated environments
- **Seccomp filtering** - Syscall filtering for additional security
- **No network access** - Sandboxed code cannot make network connections
- **Resource limits** - Memory, CPU, file size, and process limits
- **Filesystem isolation** - Cannot read sensitive files like `/etc/passwd`

## Requirements

- Ubuntu/Debian (20.04+)
- Python 3.6+
- GCC compiler
- Firejail

## Quick Start (Local Testing)

```bash
# Install dependencies
sudo apt update && sudo apt install -y gcc python3 software-properties-common

# Install firejail from PPA
sudo add-apt-repository ppa:deki/firejail
sudo apt-get update
sudo apt-get install -y firejail firejail-profiles

# Run the server
python3 server.py
```

Server runs on `http://127.0.0.1:3001`

# Run the client for local testing

python3 -m http.server

Visit `http://127.0.0.1:8000` in the browser

## Production Deployment

See [INSTALL.md](INSTALL.md) for step-by-step instructions.

### Quick Install Script

```bash
# On your VPS as root
sudo bash install.sh
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

```html
<iframe 
  src="https://c-playground.your-domain.com" 
  width="100%" 
  height="600" 
  frameborder="0"
  style="border: 1px solid #333; border-radius: 8px;">
</iframe>
```

## Security

Both **gcc** and the compiled binary run inside firejail with:

| Feature | Compile | Execute |
|---------|---------|---------|
| `--seccomp` | ✅ | ✅ |
| `--net=none` | ✅ | ✅ |
| `--caps.drop=all` | ✅ | ✅ |
| `--noroot` | ✅ | ✅ |
| `--nonewprivs` | ✅ | ✅ |
| `--private-etc` | Limited | None |
| `/usr` access | Read-only | None |
| Resource limits | ✅ | ✅ |

This prevents:
- `#include "/etc/passwd"` leaking file contents
- Network connections from compiled code
- Fork bombs and resource exhaustion
- Privilege escalation

## Troubleshooting

### "firejail: command not found"

```bash
sudo add-apt-repository ppa:deki/firejail
sudo apt-get update
sudo apt-get install -y firejail firejail-profiles
```

### "gcc: command not found"

```bash
sudo apt install -y gcc build-essential
```

### Service won't start

```bash
sudo journalctl -u c-executor -n 50
```

### Firejail permission issues

```bash
sudo chmod 4755 /usr/bin/firejail
```

## Memory Usage

- Python server: ~20-30MB
- Per compilation: ~50-100MB (temporary)
- Total: **~50-100MB** typical

Runs fine on a 1GB VPS.

## License

MIT
