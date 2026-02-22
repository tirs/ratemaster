# VPS Deployment Guide

Deploy RateMaster to a VPS (Ubuntu/Debian) using Docker Compose.

## Prerequisites

- VPS with Docker and Docker Compose
- Domain (optional, for HTTPS)

## Quick Deploy

```bash
# Clone the repo
git clone https://github.com/tirs/ratemaster.git
cd ratemaster

# Create .env from template (required before first run)
cp .env.example .env

# Edit .env: set JWT_SECRET (required), optionally ADMIN_EMAIL and ADMIN_PASSWORD
nano .env

# Build and start
docker compose up --build -d

# App: http://YOUR_VPS_IP:30000
# API: http://YOUR_VPS_IP:30080
```

## Environment Variables

Copy `.env.example` to `.env`. The following are used by Docker Compose:

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | Yes | Min 32 chars. Generate with `openssl rand -hex 32` |
| `ADMIN_EMAIL` | No | Create admin on first backend startup |
| `ADMIN_PASSWORD` | No | Admin password (set with ADMIN_EMAIL) |
| `MARKET_REFRESH_MINUTES` | No | Default 30 |
| `RATE_LIMIT_PER_MINUTE` | No | Default 120 |
| `API_CACHE_TTL_SECONDS` | No | Default 60 |

**Note:** `.env` is in `.gitignore` and is never committed. Use `.env.example` as the template.

## Production Checklist

1. **Set a strong JWT_SECRET**
   ```bash
   openssl rand -hex 32
   ```

2. **Create admin user** – Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env` before first run, or run:
   ```bash
   docker compose exec backend python -m scripts.create_admin
   ```

3. **Firewall** – Open ports 30000 (frontend) and 30080 (API) if needed.

4. **HTTPS (recommended)** – Put a reverse proxy (nginx, Caddy) in front and terminate TLS.

## Volumes

Data persists in Docker volumes:

- `postgres_data` – Database
- `uploads_data` – Organization logos and uploads

## Update from Repo

```bash
git pull origin main
docker compose up --build -d
```
