#!/bin/sh
set -e

# Render (and any other platform) can pass API_BASE_URL / WS_BASE_URL as
# plain environment variables at deploy time. This regenerates env.js
# inside the already-built dist/ folder before the static server starts,
# so no rebuild is needed to point the same image at a different backend.

: "${API_BASE_URL:=http://localhost:8000}"
: "${WS_BASE_URL:=ws://localhost:8000}"
: "${PORT:=5173}"

# Render's fromService "host" property returns a bare hostname (no scheme).
# If we were handed one, assume HTTPS/WSS, since every Render web service is
# served over TLS. Values that already include a scheme pass through as-is,
# which keeps this compatible with docker-compose's plain http/ws defaults.
case "$API_BASE_URL" in
  http://*|https://*) ;;
  *)
    case "$API_BASE_URL" in
      *.*) ;;
      *) API_BASE_URL="${API_BASE_URL}.onrender.com" ;;
    esac
    API_BASE_URL="https://${API_BASE_URL}"
    ;;
esac
case "$WS_BASE_URL" in
  ws://*|wss://*) ;;
  *)
    case "$WS_BASE_URL" in
      *.*) ;;
      *) WS_BASE_URL="${WS_BASE_URL}.onrender.com" ;;
    esac
    WS_BASE_URL="wss://${WS_BASE_URL}"
    ;;
esac

cat > /app/dist/env.js <<EOF
window.__ENV__ = {
  API_BASE_URL: "${API_BASE_URL}",
  WS_BASE_URL: "${WS_BASE_URL}",
};
EOF

exec serve -s dist -l "${PORT}"
