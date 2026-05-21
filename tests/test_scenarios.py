"""Dependency-free smoke tests for the contest scenarios."""

from __future__ import annotations

import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import run  # noqa: E402
from smart_home_agent.core.models import Intent  # noqa: E402
from smart_home_agent.core.planner import TaskPlanner  # noqa: E402


def test_sleep_mode() -> dict:
    result = run("爸妈准备睡了，帮我切到睡前模式，顺便检查一下门锁。")
    assert result["intent"]["name"] == "scene_mode_apply"
    assert result["state"]["devices"]["livingroom_tv"]["power"] == "off"
    assert result["state"]["devices"]["bedroom_ac"]["mode"] == "sleep"
    return result


def test_network_followup(state: dict) -> dict:
    first = run("爷爷房间视频有点卡，帮我看看。", state=state)
    assert first["intent"]["name"] == "network_diagnose"
    second = run("先保证爷爷那边。", state=first["state"])
    assert second["intent"]["name"] == "network_apply_qos"
    assert second["state"]["network"]["rooms"]["老人房"]["status"] == "optimized"
    return second


def test_reminder_and_knowledge(state: dict) -> None:
    reminder = run("提醒爷爷晚上九点吃降压药，如果十分钟没回应就再提醒一次。", state=state)
    assert reminder["intent"]["name"] == "reminder_create"
    query = run("爷爷今天的提醒完成了吗？", state=reminder["state"])
    assert query["intent"]["name"] == "reminder_query"
    knowledge = run("爷爷睡前能不能喝浓茶？", state=query["state"])
    assert knowledge["intent"]["name"] == "knowledge_query"
    assert "浓茶" in knowledge["reply"]


def test_reminder_complete_and_cancel() -> None:
    created = run("提醒爷爷晚上九点吃降压药，如果十分钟没回应就再提醒一次。")
    completed = run("爷爷已经吃过药了", state=created["state"])
    assert completed["intent"]["name"] == "reminder_complete"
    updated = completed["tool_results"][0]["data"]["updated"]
    assert updated and updated[0]["completed"] is True

    canceled = run("取消爷爷今晚吃药提醒", state=completed["state"])
    assert canceled["intent"]["name"] == "reminder_cancel"
    canceled_items = canceled["tool_results"][0]["data"]["updated"]
    assert canceled_items and canceled_items[0]["canceled"] is True


def test_knowledge_rejects_unsupported_question() -> None:
    result = run("爷爷睡前能不能吃榴莲？", config={"enable_local_llm": False})
    assert result["intent"]["name"] == "knowledge_query"
    assert result["tool_results"][0]["data"]["hits"] == []
    assert "不会编造" in result["reply"]


def test_knowledge_miss_falls_back_to_llm_answer() -> None:
    result = run("可乐鸡翅怎么做")
    assert result["intent"]["name"] == "knowledge_query"
    assert result["tool_results"][0]["data"]["hits"] == []
    assert result["metrics"]["answer_model_attempted"] is True
    assert "鸡翅" in result["reply"]


def test_family_profile_long_term_memory() -> None:
    db_path = Path(tempfile.gettempdir()) / f"smart_home_profile_test_{uuid.uuid4().hex}.db"
    cfg = {"sqlite_path": str(db_path), "enable_local_llm": False}
    remembered = run("记住爷爷喜欢吃清淡的，不吃辣，性格比较节俭。", config=cfg)
    assert remembered["intent"]["name"] == "profile_memory_update"
    assert "已记住" in remembered["reply"]
    assert "不吃辣" in str(remembered["state"]["family_profiles"]["爷爷"])

    queried = run("爷爷喜欢吃什么？", state={}, config=cfg)
    assert queried["intent"]["name"] == "profile_memory_query"
    assert "清淡" in queried["reply"]
    assert "不吃辣" in queried["reply"]


def test_profile_memory_overrides_force_llm_mode() -> None:
    db_path = Path(tempfile.gettempdir()) / f"smart_home_profile_force_{uuid.uuid4().hex}.db"
    cfg = {"sqlite_path": str(db_path), "mode": "llm", "force_local_llm": True, "enable_local_llm": True}
    result = run("记住奶奶喜欢吃番茄炒蛋", config=cfg)
    assert result["intent"]["name"] == "profile_memory_update"
    assert result["intent"]["source"] == "rule"
    assert result["tool_results"][0]["tool"] == "profile.remember"
    assert "番茄炒蛋" in str(result["state"]["family_profiles"].get("奶奶"))


def test_safety_confirmation() -> None:
    blocked = run("帮我把门锁解锁。")
    assert blocked["safety"]["need_confirmation"] is True
    confirmed = run("确认执行", state=blocked["state"])
    assert confirmed["state"]["devices"]["front_door_lock"]["locked"] is False


def test_child_mode() -> None:
    result = run("给孩子开学习模式")
    assert result["intent"]["name"] == "child_mode_apply"
    assert result["state"]["devices"]["kids_room_light"]["brightness"] == 75
    assert result["state"]["timers"], "应当生成护眼休息定时器"


def test_energy_query() -> None:
    result = run("查一下今天家里的能耗排行")
    assert result["intent"]["name"] == "energy_query"
    energy_step = next(r for r in result["tool_results"] if r["tool"] == "energy.query")
    assert energy_step["data"]["ranking"], "应有能耗排行"
    assert "kWh" in result["reply"]


def test_proactive_alert() -> None:
    result = run("一键巡检家里有没有异常")
    assert result["intent"]["name"] == "proactive_alert"
    alert_step = next(r for r in result["tool_results"] if r["tool"] == "sensor.check_alert")
    assert len(alert_step["data"]["alerts"]) >= 1


def test_sensor_query() -> None:
    result = run("看看老人房怎么样")
    assert result["intent"]["name"] == "sensor_query"
    assert "老人房" in result["reply"]


def test_temperature_query_uses_sensors() -> None:
    result = run("今天温度是多少", config={"enable_local_llm": False})
    assert result["intent"]["name"] == "sensor_query"
    assert "全屋环境" in result["reply"]
    assert "℃" in result["reply"]


def test_room_home_status_uses_room_sensor_and_device_tools() -> None:
    intent = Intent("home_status_query", 0.95, {"room": "老人房"})
    steps = TaskPlanner().build(intent, {}, {})
    tools = [step.tool for step in steps]
    assert tools == ["home_profile.query", "sensor.query", "device.query"]
    assert steps[1].args["room"] == "老人房"
    assert steps[2].args["room"] == "老人房"


if __name__ == "__main__":
    state = test_sleep_mode()["state"]
    state = test_network_followup(state)["state"]
    test_reminder_and_knowledge(state)
    test_reminder_complete_and_cancel()
    test_knowledge_rejects_unsupported_question()
    test_knowledge_miss_falls_back_to_llm_answer()
    test_family_profile_long_term_memory()
    test_profile_memory_overrides_force_llm_mode()
    test_safety_confirmation()
    test_child_mode()
    test_energy_query()
    test_proactive_alert()
    test_sensor_query()
    test_temperature_query_uses_sensors()
    test_room_home_status_uses_room_sensor_and_device_tools()
    print("all scenario tests passed")
