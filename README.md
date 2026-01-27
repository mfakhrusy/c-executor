# Wasmer Clang Test

A minimal test project to verify Wasmer SDK works with proper COEP/COOP headers on Caddy.

## Required Headers

The Wasmer SDK requires these headers for `SharedArrayBuffer` support:

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: credentialless
```

Note: `credentialless` is used instead of `require-corp` to avoid CORS issues with Wasmer's CDN.

## Local Testing with Caddy

### 1. Install Caddy

```bash
# Ubuntu/Debian
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Or download binary from https://caddyserver.com/download
```

### 2. Run locally

```bash
cd /home/fahru/wasmer-test
caddy run --config Caddyfile
```

Open http://localhost:8080 in your browser.

## Production Deployment (VPS)

### 1. Copy files to server

```bash
scp -r /home/fahru/wasmer-test user@your-server:/var/www/wasmer-test
scp /home/fahru/wasmer-test/Caddyfile user@your-server:/etc/caddy/Caddyfile
```

### 2. Edit Caddyfile on server

Replace `your-domain.com` with your actual domain:

```bash
sudo nano /etc/caddy/Caddyfile
```

Update the domain and file path:

```
your-actual-domain.com {
    root * /var/www/wasmer-test
    file_server

    header {
        Cross-Origin-Opener-Policy "same-origin"
        Cross-Origin-Embedder-Policy "credentialless"
    }
}
```

### 3. Restart Caddy

```bash
sudo systemctl restart caddy
```

Caddy will automatically obtain SSL certificates from Let's Encrypt.

### 4. Verify headers

```bash
curl -I https://your-domain.com
```

You should see:
```
cross-origin-opener-policy: same-origin
cross-origin-embedder-policy: credentialless
```

## Troubleshooting

### CORS errors from cdn.wasmer.io

If you see CORS errors fetching from `cdn.wasmer.io`, ensure you're using:
- `Cross-Origin-Embedder-Policy: credentialless` (not `require-corp`)

### SharedArrayBuffer is not defined

This means the COEP/COOP headers are not being applied. Verify:
1. You're accessing via HTTPS (or localhost)
2. Headers are correctly set (check with browser DevTools → Network tab)

### Browser compatibility

`credentialless` COEP mode requires:
- Chrome 96+
- Firefox 97+
- Safari 15.2+
