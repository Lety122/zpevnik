#!/bin/bash
# Deploy zpevnik to VPS (canonical: https://zpevnik.droplet.cz)
# Renders songs from song.pro, regenerates song list + SW cache (py-gen.py bumps cache
# version), then rsyncs only the static site to the web root.
# Prerequisite (one-time): sudo chown -R pavel:pavel /var/www/zpevnik.jelinekp.cz
set -euo pipefail
cd "$(dirname "$0")"

python3 py-gen.py

rsync -av --delete \
  --exclude '.git' --exclude 'deploy.sh' \
  --exclude 'py-gen.py' --exclude 'chordpro.py' \
  --exclude 'convert_to_chordpro.py' --exclude 'verify_conversion.py' \
  --exclude '*.pro' --exclude 'tests' --exclude 'docs' \
  ./ pavel-vps:/var/www/zpevnik.jelinekp.cz/

echo "Deployed: https://zpevnik.droplet.cz"
echo "Nezapomeň commitnout: git add -A && git commit"
