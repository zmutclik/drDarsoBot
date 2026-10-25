#!/usr/bin/env bash
# Sajikan folder wireframe lewat HTTP di port 8036
cd "$(dirname "$0")" || exit 1
PORT=8036
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo "Prototype: http://${IP:-localhost}:${PORT}/prototype/"
exec python3 -m http.server "$PORT" --bind 0.0.0.0
