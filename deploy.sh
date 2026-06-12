#!/bin/bash
# Deploy zpevnik to VPS (https://zpevnik.jelinekp.cz)
# Regenerates song list + SW cache (py-gen.py bumps cache version), then rsyncs.
# Prerequisite (one-time): sudo chown -R pavel:pavel /var/www/zpevnik.jelinekp.cz
set -euo pipefail
cd "$(dirname "$0")"

python3 py-gen.py

rsync -av --delete \
  --exclude '.git' --exclude 'py-gen.py' --exclude 'předloha.html' \
  --exclude 'deploy.sh' \
  ./ pavel-vps:/var/www/zpevnik.jelinekp.cz/

echo "Deployed: https://zpevnik.jelinekp.cz"
echo "Nezapomeň commitnout: git add -A && git commit"
