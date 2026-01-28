# C Playground

A sandboxed C code execution service using Python + GCC + bubblewrap. Designed to be embedded as an iframe in blogs.

**Live demo:** [c-playground.fahru.me](https://c-playground.fahru.me)

<img width="1595" height="648" alt="image" src="https://github.com/user-attachments/assets/5b6e0c4e-42d3-46e2-b813-576715dc59eb" />

## Features

- **Bubblewrap sandbox** - Both compilation and execution run in isolated containers
- **No network access** - Sandboxed code cannot make network connections
- **Read-only filesystem** - Only temp directory is writable
- **Resource limits** - Memory and CPU limits via systemd
- **Iframe-friendly** - Designed for embedding in blogs

## Requirements

- Ubuntu/Debian (20.04+)
- Python 3.6+
- GCC compiler
- Bubblewrap

## Quick Start (Local Testing)

```bash
# Install dependencies
sudo apt update && sudo apt install -y gcc python3 bubblewrap

# Run the server
python3 server.py
```

Server runs on `http://127.0.0.1:3001`

On a different terminal tab:

```bash
python3 -m http.server
```

Visit `http://127.0.0.1:8000` in the browser.

## Production Deployment

See [INSTALL.md](INSTALL.md) for step-by-step instructions.

### Quick Install Script

```bash
# Clone to your server
git clone https://github.com/mfakhrusy/c-playground-wasmer.git
cd c-playground-wasmer
sudo bash install.sh
```

Then configure your Caddy reverse proxy manually.

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
  "stderr": "main.c:1:1: error: ...",
  "exit_code": 1
}
```

## Embedding in Your Blog (iframe)

```html
<iframe 
  src="https://c-playground.fahru.me" 
  width="100%" 
  height="600" 
  frameborder="0"
  style="border: 1px solid #333; border-radius: 8px;">
</iframe>
```

## Security

Both **GCC** and the compiled binary run inside bubblewrap with:

| Feature | Description |
|---------|-------------|
| `--tmpfs /` | Temporary root filesystem |
| `--ro-bind` | Read-only system directories |
| `--unshare-pid` | Isolated PID namespace |
| `--die-with-parent` | Kill if server dies |
| No network | No network namespace mounted |

This prevents:
- `#include "/etc/passwd"` leaking file contents (read-only binds)
- Fork bombs and resource exhaustion (systemd limits)
- Privilege escalation

## Troubleshooting

### "bwrap: command not found"

```bash
sudo apt install -y bubblewrap
```

### Service won't start

```bash
sudo journalctl -u c-executor -n 50
```

## Memory Usage

- Python server: ~20-30MB
- Per compilation: ~50-100MB (temporary)
- Total: **~50-100MB** typical

Runs fine on a 1GB VPS.

## License

MIT
