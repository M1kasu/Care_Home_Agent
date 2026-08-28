#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/3] Restarting ESPHome virtual devices..."
docker compose restart presence-node light-node curtain-node ac-node

echo "[2/3] Waiting for device initialization..."
sleep 12

echo "[3/3] Current containers:"
docker compose ps

echo
echo "Expected state:"
echo "  Presence = ON"
echo "  Light    = ON / 80%"
echo "  Curtain  = OPEN / 100%"
echo "  AC       = COOL, target 26 C"
echo "  Temp     = cooling from 30.2 C"
