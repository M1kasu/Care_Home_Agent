"""Download Qwen2.5-1.5B-Instruct Q4_K_M GGUF model for local inference."""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent.parent / "smart_home_agent" / "data"
MODEL_FILE = MODEL_DIR / "qwen2.5-1.5b-instruct-q4_k_m.gguf"

# Qwen2.5-1.5B-Instruct Q4_K_M from bartowski on HuggingFace
DOWNLOAD_URL = (
    "https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF/"
    "resolve/main/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"
)

CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB


def main() -> None:
    if MODEL_FILE.exists():
        size_mb = MODEL_FILE.stat().st_size / (1024 * 1024)
        print(f"Model already exists: {MODEL_FILE} ({size_mb:.0f} MB)")
        return

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    tmp_file = MODEL_FILE.with_suffix(".gguf.part")

    print(f"Downloading Qwen2.5-1.5B-Instruct Q4_K_M...")
    print(f"  URL: {DOWNLOAD_URL}")
    print(f"  Target: {MODEL_FILE}")

    try:
        req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "Mozilla/5.0"})
        existing = tmp_file.stat().st_size if tmp_file.exists() else 0
        if existing:
            req.add_header("Range", f"bytes={existing}-")
            print(f"  Resuming from {existing / (1024*1024):.0f} MB...")

        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            if existing and resp.status == 206:
                total += existing
            downloaded = existing
            with open(tmp_file, "ab") as f:
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r  Progress: {downloaded/(1024*1024):.0f}/{total/(1024*1024):.0f} MB ({pct:.1f}%)", end="", flush=True)
            print()

        tmp_file.rename(MODEL_FILE)
        final_mb = MODEL_FILE.stat().st_size / (1024 * 1024)
        print(f"Done: {MODEL_FILE} ({final_mb:.0f} MB)")

    except Exception as exc:
        print(f"\nDownload failed: {exc}")
        print("You can manually download from:")
        print(f"  {DOWNLOAD_URL}")
        print(f"and place it at: {MODEL_FILE}")
        sys.exit(1)


if __name__ == "__main__":
    main()
