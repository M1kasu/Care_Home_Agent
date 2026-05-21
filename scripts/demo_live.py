"""Offline live demo for the smart-home contest agent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import run  # noqa: E402


SCENARIOS = [
    "爸妈准备睡了，帮我切到睡前模式，顺便检查一下门锁。",
    "爷爷房间视频有点卡，帮我看看。",
    "先保证爷爷那边。",
    "提醒爷爷晚上九点吃降压药，如果十分钟没回应就再提醒一次。",
    "爷爷今天的提醒完成了吗？",
    "爷爷睡前能不能喝浓茶？",
    "看看老人房现在怎么样？",
    "一键巡检家里有没有异常。",
    "给孩子开学习模式。",
    "查一下今天家里的能耗排行。",
    "帮我把门锁解锁。",
    "确认执行",
]


def main() -> None:
    state = None
    for index, user_input in enumerate(SCENARIOS, start=1):
        result = run(user_input, state=state)
        state = result["state"]
        print(f"\n## Round {index}")
        print(f"User: {user_input}")
        print(f"Agent: {result['reply']}")
        print("Intent:", result["intent"]["name"], "confidence=", result["intent"]["confidence"])
        print("Plan:", ", ".join(step["tool"] for step in result["plan"]) or "none")
        print("Metrics:", json.dumps(result["metrics"], ensure_ascii=False))


if __name__ == "__main__":
    main()
