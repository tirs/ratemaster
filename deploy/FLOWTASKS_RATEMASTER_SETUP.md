# Add RateMaster to FlowTasks (Option B – Full Setup)

When flowtasks frontend is the main nginx (ports 80/443), follow these steps to add ratemaster with SSL.

## Step 1: Get the ratemaster SSL cert

Stop the flowtasks frontend so port 80 is free for certbot:

```bash
cd /opt/flowtasks
docker compose stop frontend

sudo certbot certonly --standalone -d ratemaster.flowtasks.io
# Enter email, agree to terms when prompted

# Verify cert exists
sudo ls -la /etc/letsencrypt/live/ratemaster.flowtasks.io/
```

## Step 2: Add volume mounts to flowtasks docker-compose

Edit the flowtasks docker-compose:

```bash
sudo nano /opt/flowtasks/docker-compose.yml
```

Find the frontend service `volumes` section (it already has flowtasks.io and formforge certs). Add these two lines:

```yaml
      - /etc/letsencrypt/live/ratemaster.flowtasks.io/fullchain.pem:/etc/nginx/ssl/ratemaster-fullchain.pem:ro
      - /etc/letsencrypt/live/ratemaster.flowtasks.io/privkey.pem:/etc/nginx/ssl/ratemaster-privkey.pem:ro
```

## Step 3: Add ratemaster block to flowtasks nginx.conf

Edit the flowtasks nginx config:

```bash
sudo nano /opt/flowtasks/frontend/nginx.conf
```

Add this server block (use `host.docker.internal` so the container can reach ratemaster on the host):

```nginx
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name ratemaster.flowtasks.io;

    ssl_certificate /etc/nginx/ssl/ratemaster-fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/ratemaster-privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 10M;

    location / {
        proxy_pass http://host.docker.internal:30000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Step 4: Rebuild and start

```bash
cd /opt/flowtasks
docker compose build frontend --no-cache
docker compose up -d
```

## Step 5: Ensure ratemaster is running

```bash
cd ~/ratemaster
docker compose up -d
```

## Step 6: Verify

- https://ratemaster.flowtasks.io
- https://flow.flowtasks.io (and other sites)

---

## Deploy updates (after code changes)

From your dev machine, push to GitHub:
```bash
git add -A && git commit -m "Your message" && git push origin main
```

On the VPS:
```bash
cd ~/ratemaster
chmod +x deploy.sh   # first time only
./deploy.sh
# Or manually:
git pull origin main
docker compose up --build -d
```
