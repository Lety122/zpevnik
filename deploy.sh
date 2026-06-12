#!/bin/bash
# Deploy zpevnik to VPS (https://zpevnik.jelinekp.cz)
# Prerequisite (one-time): sudo chown -R pavel:pavel /var/www/zpevnik.jelinekp.cz
set -euo pipefail
cd "$(dirname "$0")"

if ! grep -q "zpevnik-cache-v" sw.js; then
  echo "sw.js missing CACHE_NAME?" >&2; exit 1
fi
echo "Current cache version: $(grep -o "zpevnik-cache-v[0-9]*" sw.js | head -1)"
echo "(Did you bump CACHE_NAME after content changes? Ctrl+C to abort)"
sleep 3

rsync -av --delete \
  --exclude '.git' --exclude 'py-gen.py' --exclude 'předloha.html' \
  --exclude 'deploy.sh' \
  ./ pavel-vps:/var/www/zpevnik.jelinekp.cz/

echo "Deployed: https://zpevnik.jelinekp.cz"
