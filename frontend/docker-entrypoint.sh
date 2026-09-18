#!/bin/sh
set -e

: "${API_BASE_URL:=http://localhost:8000}"
: "${WS_BASE_URL:=ws://localhost:8000}"
: "${PORT:=5173}"

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
