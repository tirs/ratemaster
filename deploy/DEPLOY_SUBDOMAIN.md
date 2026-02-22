# Deploy RateMaster as ratemaster.flowtasks.io

Deploy RateMaster as a subdomain on your existing VPS (flowtasks.io) with Nginx and Cloudflare.

## 1. Cloudflare DNS

In Cloudflare dashboard for **flowtasks.io**:

1. Go to **DNS** → **Records**
2. Add record:
   - **Type:** `A`
   - **Name:** `ratemaster`
   - **IPv4 address:** Your VPS IP
   - **Proxy status:** Proxied (orange cloud) for DDoS protection and SSL, or DNS only (grey) if Nginx handles SSL
3. Save

Result: `ratemaster.flowtasks.io` → your VPS

**Note:** If using Cloudflare proxy (orange cloud), Cloudflare terminates SSL. Use "Full" or "Full (strict)" SSL mode in Cloudflare. Your Nginx can use HTTP to localhost or Cloudflare Origin Certificate for encryption to Cloudflare.

## 2. Clone and Configure on VPS

```bash
cd ~   # /root – alongside flow-rag, formforge-legal, nba-prop-engine (opt is for main site only)
git clone git@github.com:tirs/ratemaster.git
cd ratemaster
```

The repo includes `.env`. Verify `JWT_SECRET` is set.

## 3. Nginx + SSL

You have per-subdomain certs (flow, formforge, nba). Get one for ratemaster, then enable the full config:

```bash
cd ~/ratemaster

# 1. Bootstrap (HTTP only) - nginx won't start without the cert, so use this first
sudo cp deploy/nginx-ratemaster-bootstrap.conf /etc/nginx/sites-available/ratemaster
sudo ln -sf /etc/nginx/sites-available/ratemaster /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 2. Get cert
sudo certbot certonly --nginx -d ratemaster.flowtasks.io

# 3. Switch to full config with SSL
sudo cp deploy/nginx-ratemaster.conf /etc/nginx/sites-available/ratemaster
sudo nginx -t && sudo systemctl reload nginx
```

## 4. Docker Compose (Bind to Localhost)

RateMaster binds to `127.0.0.1` so only Nginx can reach it (no public ports):

```bash
cd ~/ratemaster
docker compose up --build -d
```

Ports used internally:
- `127.0.0.1:30000` – Frontend (Next.js)
- `127.0.0.1:30080` – Backend API (only if you need direct API access; frontend proxies /api/v1)

If ports 30000/30080 conflict with other apps, edit `docker-compose.yml` and change the host ports (e.g. `127.0.0.1:30100:30000`).

## 5. Verify

- **App:** https://ratemaster.flowtasks.io
- **API docs:** https://ratemaster.flowtasks.io/api/v1/docs (or /openapi.json)

## 6. Create Admin

```bash
cd ~/ratemaster
docker compose exec backend python -m scripts.create_admin
# Or set ADMIN_EMAIL and ADMIN_PASSWORD in .env before first run
```

## 7. Update from Repo

```bash
cd ~/ratemaster
git pull origin main
docker compose up --build -d
```
