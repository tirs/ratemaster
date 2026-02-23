#!/bin/bash
# Deploy RateMaster on VPS - run from ~/ratemaster
set -e
cd "$(dirname "$0")"
echo "Pulling latest..."
git fetch origin
git reset --hard origin/main
echo "Rebuilding and starting..."
docker compose up --build -d
echo "Done. Ratemaster is up at https://ratemaster.flowtasks.io"
