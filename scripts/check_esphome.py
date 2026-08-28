"""Read-only connectivity and entity diagnostic for the ESPHome backend."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from smart_home_agent.home_runtime.integrations.esphome import (
    ESPHomeBridge,
    default_nodes,
)


def main() -> int:
    host = os.getenv("ESPHOME_HOST", "192.168.111.134")
    noise_psk = os.getenv("ESPHOME_NOISE_PSK", "").strip()
    if not noise_psk:
        print("Missing ESPHOME_NOISE_PSK environment variable.", file=sys.stderr)
        return 2

    bridge = ESPHomeBridge(default_nodes(host), noise_psk)
    bridge.start()
    ready = bridge.wait_ready(float(os.getenv("ESPHOME_CONNECT_TIMEOUT", "12")))
    payload = {
        "ready": ready,
        "status": bridge.status(),
        "devices": bridge.device_states(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    bridge.stop()
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
