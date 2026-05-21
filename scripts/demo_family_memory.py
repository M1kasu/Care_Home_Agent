"""Demo persistent family profile memory."""

from __future__ import annotations

import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import run  # noqa: E402


def main() -> None:
    state = None
    db_path = Path(tempfile.gettempdir()) / f"smart_home_family_memory_demo_{uuid.uuid4().hex}.db"
    config = {"sqlite_path": str(db_path)}
    prompts = [
        "记住爷爷喜欢吃清淡的，不吃辣，性格比较节俭。",
        "记住妈妈喜欢看电影，性格比较急。",
        "爷爷喜欢吃什么？",
        "中午给家里吃什么好？",
    ]
    for text in prompts:
        result = run(text, state=state, config=config)
        state = result["state"]
        print("=" * 80)
        print("User:", text)
        print("Intent:", result["intent"]["name"])
        print("Reply:", result["reply"])
        print("Profiles:", result["state"].get("family_profiles", {}))


if __name__ == "__main__":
    main()
