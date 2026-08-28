#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

test -f esphome/secrets.yaml || {
  echo "Missing esphome/secrets.yaml; copy secrets.example.yaml first." >&2
  exit 1
}

for device in light curtain presence ac; do
  echo "========== ${device}.yaml =========="
  docker compose run --rm --no-deps "${device}-node" config "/config/${device}.yaml"
done
