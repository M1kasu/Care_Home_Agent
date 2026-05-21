"""Rule-first intent router with optional local Ollama fallback."""

from __future__ import annotations

import re
import time
from typing import Any

from ..memory.session import SessionMemory
from ..providers.local_llm import get_cached_local_llm_client
from .models import Intent

CHINESE_NUMBERS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}

ALLOWED_INTENTS = {
    "scene_mode_apply",
    "device_control",
    "network_diagnose",
    "network_apply_qos",
    "reminder_create",
    "reminder_query",
    "reminder_complete",
    "reminder_cancel",
    "knowledge_query",
    "home_status_query",
    "child_mode_apply",
    "energy_query",
    "sensor_query",
    "proactive_alert",
    "profile_memory_update",
    "profile_memory_query",
    "unknown",
}

PROTECTED_RULE_INTENTS = {
    "confirmation_accept",
    "confirmation_reject",
    "reminder_complete",
    "reminder_cancel",
    "profile_memory_update",
    "profile_memory_query",
}


class LocalRouter:
    def __init__(self, memory: SessionMemory) -> None:
        self._memory = memory

    def route(self, text: str, state: dict[str, Any], config: dict[str, Any]) -> tuple[Intent, dict[str, Any]]:
        start = time.perf_counter()
        normalized = _normalize(text)
        force_local_llm = bool(config.get("force_local_llm") or config.get("mode") in {"llm", "local_llm"})
        model_metrics: dict[str, Any] = {
            "model_latency_ms": 0,
            "model_attempted": False,
            "model_available": False,
            "model_error": "",
            "model_raw_output": "",
        }

        intent = self._rule_route(normalized, state)
        if intent.name in PROTECTED_RULE_INTENTS:
            metrics = {
                "nlu_latency_ms": int((time.perf_counter() - start) * 1000),
                **model_metrics,
            }
            return intent, metrics

        if force_local_llm and config.get("enable_local_llm"):
            model_intent, model_metrics = self._local_llm_route(text, normalized, state, config, forced=True)
            if model_intent is not None:
                intent = model_intent
        elif intent.name == "unknown" and config.get("mode") == "hybrid" and config.get("enable_local_llm"):
            model_intent, model_metrics = self._local_llm_route(text, normalized, state, config, forced=False)
            if model_intent is not None:
                intent = model_intent
        metrics = {
            "nlu_latency_ms": int((time.perf_counter() - start) * 1000),
            **model_metrics,
        }
        return intent, metrics

    def _local_llm_route(
        self,
        text: str,
        normalized: str,
        state: dict[str, Any],
        config: dict[str, Any],
        *,
        forced: bool,
    ) -> tuple[Intent | None, dict[str, Any]]:
        model_start = time.perf_counter()
        client = get_cached_local_llm_client(config)
        model_result = client.classify_intent(text, self._memory.recent_text(state))
        model_latency_ms = int((time.perf_counter() - model_start) * 1000)
        status = client.status()
        metrics = {
            "model_latency_ms": model_latency_ms,
            "model_attempted": True,
            "model_available": bool(status.get("available")),
            "model_error": str(status.get("load_error") or ""),
            "model_raw_output": client.last_raw_output,
            "model_cache_hit": bool(getattr(client, "last_cache_hit", False)),
        }
        if not model_result:
            return None, metrics
        confidence = _normalize_confidence(model_result.get("confidence"))
        min_confidence = float(config.get("llm_min_confidence", 0.55))
        name = str(model_result.get("name") or "unknown")
        if name not in ALLOWED_INTENTS:
            return None, metrics
        if name == "unknown" or confidence < min_confidence:
            return None, metrics
        reason = "强制使用本地 Qwen 模型识别意图" if forced else "规则未命中，使用本地 Qwen 模型兜底识别"
        return (
            Intent(
                name=name,
                confidence=confidence,
                slots={**self._extract_slots(normalized, state), **dict(model_result.get("slots") or {})},
                source="local_llm",
                reasoning=reason,
            ),
            metrics,
        )

    def _rule_route(self, text: str, state: dict[str, Any]) -> Intent:
        slots = self._extract_slots(text, state)
        pending = bool(state.get("pending_confirmations"))
        if pending and _has_any(text, ["确认", "同意", "可以", "执行", "继续"]):
            return Intent("confirmation_accept", 0.99, slots, reasoning="用户确认执行待审批动作")
        if pending and _has_any(text, ["取消", "不用", "不要", "拒绝"]):
            return Intent("confirmation_reject", 0.99, slots, reasoning="用户取消待审批动作")
        if _is_profile_memory_update(text, state):
            return Intent("profile_memory_update", 0.96, slots, reasoning="用户显式要求记住家庭成员画像")
        if _is_profile_memory_query(text, state):
            return Intent("profile_memory_query", 0.92, slots, reasoning="用户查询长期家庭画像")
        if _has_any(text, ["先保证", "优先", "保证爷爷", "保证老人"]) and (
            state.get("last_task", {}).get("intent") == "network_diagnose" or state.get("last_room")
        ):
            slots["room"] = slots.get("room") or state.get("last_room") or "老人房"
            slots["policy"] = "video_call_first"
            return Intent("network_apply_qos", 0.96, slots, reasoning="多轮继承上一轮网络诊断上下文")
        if _has_any(text, ["节能", "电费", "能耗", "用电", "耗电", "待机"]) or (
            _has_any(text, ["电"]) and _has_any(text, ["多少", "排行", "什么耗"])
        ):
            return Intent("energy_query", 0.92, slots, reasoning="命中家庭能源管理关键词")
        if _has_any(text, ["护眼", "用眼", "学习模式", "写作业"]) or (
            ("孩子" in text or "儿童" in text) and _has_any(text, ["学习", "睡觉", "睡眠", "看电视"])
        ):
            slots.setdefault("scene", "child_sleep" if _has_any(text, ["睡觉", "睡眠"]) else "child_study")
            return Intent("child_mode_apply", 0.93, slots, reasoning="命中儿童护眼/学习模式关键词")
        if _has_any(text, ["传感器", "温度", "多少度", "室温", "冷不冷", "热不热", "湿度", "有人吗", "老人怎么样", "爷爷怎么样", "看看老人房"]):
            return Intent("sensor_query", 0.9, slots, reasoning="命中传感器/环境查询关键词")
        if _has_any(text, ["主动提醒", "有什么异常", "异常", "安全吗", "看看有没有问题", "检查家里", "一键巡检"]):
            return Intent("proactive_alert", 0.9, slots, reasoning="命中主动感知/巡检关键词")
        if _is_reminder_cancel(text):
            return Intent("reminder_cancel", 0.95, slots, reasoning="用户要求取消提醒")
        if _is_reminder_complete(text):
            return Intent("reminder_complete", 0.95, slots, reasoning="用户确认提醒事项已完成")
        if "提醒" in text and not _has_any(text, ["完成了吗", "了吗", "查询", "今天的提醒"]):
            return Intent("reminder_create", 0.94, slots, reasoning="命中提醒创建关键词")
        if _has_any(text, ["吃药了吗", "提醒完成", "今天的提醒", "完成了吗"]):
            return Intent("reminder_query", 0.94, slots, reasoning="命中提醒查询关键词")
        if _has_any(text, ["wifi", "wi-fi", "网络", "信号", "卡", "卡顿", "掉线", "延迟", "mesh", "视频"]):
            return Intent("network_diagnose", 0.91, slots, reasoning="命中家庭网络诊断关键词")
        if _has_any(text, ["睡前", "离家", "回家", "观影", "学习"]) and _has_any(text, ["模式", "切", "准备", "帮我"]):
            return Intent("scene_mode_apply", 0.93, slots, reasoning="命中场景模式关键词")
        if _has_any(text, ["灯", "空调", "电视", "门锁", "摄像头"]) and _has_any(text, ["打开", "关", "关闭", "调", "锁", "解锁"]):
            return Intent("device_control", 0.9, slots, reasoning="命中设备控制关键词")
        if _is_home_knowledge_question(text):
            return Intent("knowledge_query", 0.86, slots, reasoning="命中本地知识问答关键词")
        if _is_home_status_query(text):
            return Intent("home_status_query", 0.82, slots, reasoning="命中家庭状态查询关键词")
        return Intent("unknown", 0.35, slots, reasoning="规则未找到稳定意图")

    def _extract_slots(self, text: str, state: dict[str, Any]) -> dict[str, Any]:
        slots: dict[str, Any] = {"raw_text": text}
        members = []
        if "爸妈" in text or "父母" in text:
            members.extend(["爸爸", "妈妈"])
            slots["member_group"] = "爸妈"
            slots["room"] = "主卧"
        for member in ["爷爷", "奶奶", "爸爸", "妈妈", "孩子"]:
            if member in text and member not in members:
                members.append(member)
        if members:
            slots["members"] = members
            slots["member"] = members[0]
            room = state.get("family", {}).get("members", {}).get(members[0], {}).get("room")
            if room:
                slots.setdefault("room", room)
        room_aliases = {
            "老人房": "老人房",
            "爷爷房": "老人房",
            "爷爷房间": "老人房",
            "老人那边": "老人房",
            "爷爷那边": "老人房",
            "卧室": "主卧",
            "主卧": "主卧",
            "客厅": "客厅",
            "儿童房": "儿童房",
            "孩子房": "儿童房",
            "玄关": "玄关",
        }
        for alias, room in room_aliases.items():
            if alias in text:
                slots["room"] = room
                break
        scene_map = {"睡前": "sleep", "离家": "away", "回家": "home", "观影": "movie", "学习": "child_study", "写作业": "child_study", "护眼": "child_study"}
        for word, scene in scene_map.items():
            if word in text:
                slots["scene"] = scene
                break
        if _has_any(text, ["孩子睡", "儿童睡", "哄孩子"]):
            slots["scene"] = "child_sleep"
        device_map = {"灯": "灯", "空调": "空调", "电视": "电视", "门锁": "门锁", "锁": "门锁", "摄像头": "摄像头"}
        for word, device in device_map.items():
            if word in text:
                slots["device"] = device
                break
        action, value = self._extract_action(text)
        if action:
            slots["action"] = action
        if value is not None:
            slots["value"] = value
        time_value = _extract_time(text)
        if time_value:
            slots["time"] = time_value
        retry = _extract_retry_minutes(text)
        if retry:
            slots["retry_after_min"] = retry
        reminder_id = _extract_reminder_id(text)
        if reminder_id:
            slots["reminder_id"] = reminder_id
        if _has_any(text, ["全部", "所有"]):
            slots["all"] = True
        if _has_any(text, ["降压药", "吃药", "药"]):
            slots["task"] = "吃降压药" if "降压药" in text else "吃药"
        if _has_any(text, ["爷爷", "奶奶", "老人"]):
            slots["priority"] = "elderly"
        if _has_any(text, ["视频", "通话"]):
            slots["symptom"] = "video_lag"
        return slots

    @staticmethod
    def _extract_action(text: str) -> tuple[str | None, Any]:
        if "解锁" in text:
            return "unlock", None
        if "锁门" in text or "上锁" in text or "门锁锁" in text:
            return "lock", None
        if "调暗" in text:
            return "set_brightness", 20
        brightness = re.search(r"(\d{1,3})%", text)
        if brightness:
            return "set_brightness", min(100, int(brightness.group(1)))
        temperature = re.search(r"(\d{2})度", text)
        if temperature:
            return "set_temperature", int(temperature.group(1))
        if "睡眠模式" in text:
            return "set_mode", "sleep"
        if _has_any(text, ["关闭", "关掉", "关上", "关"]):
            return "turn_off", None
        if _has_any(text, ["打开", "开启", "开"]):
            return "turn_on", None
        return None, None


def _normalize(text: str) -> str:
    return text.strip().lower().replace(" ", "").replace("wi-fi", "wifi")


def _has_any(text: str, words: list[str]) -> bool:
    return any(word.lower() in text for word in words)


def _normalize_confidence(value: Any) -> float:
    try:
        confidence = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    if confidence > 1.0 and confidence <= 100.0:
        confidence = confidence / 100.0
    return max(0.0, min(1.0, confidence))


def _is_home_status_query(text: str) -> bool:
    explicit_phrases = [
        "家里现在状态",
        "家里状态",
        "全屋状态",
        "家庭状态",
        "有哪些设备",
        "设备状态",
    ]
    if _has_any(text, explicit_phrases):
        return True
    return _has_any(text, ["哪些", "什么"]) and _has_any(text, ["设备", "开着", "打开"])


def _is_reminder_cancel(text: str) -> bool:
    if not _has_any(text, ["提醒", "闹钟", "吃药"]):
        return False
    return _has_any(text, ["取消", "删掉", "删除", "不用提醒", "不要提醒", "撤销"])


def _is_reminder_complete(text: str) -> bool:
    if _has_any(text, ["完成了吗", "吃药了吗", "了吗", "查询", "查一下"]):
        return False
    if _has_any(text, ["吃过了", "已经吃", "已吃", "吃了药", "药吃了"]):
        return True
    return _has_any(text, ["提醒"]) and _has_any(text, ["完成了", "已完成", "打卡", "确认完成"])


def _is_home_knowledge_question(text: str) -> bool:
    question_words = ["能不能", "可以", "怎么", "为什么", "注意", "说明", "建议", "要不要", "是否"]
    domain_words = [
        "老人",
        "爷爷",
        "奶奶",
        "睡前",
        "浓茶",
        "空调",
        "睡眠",
        "wifi",
        "网络",
        "mesh",
        "qos",
        "门锁",
        "解锁",
        "护眼",
        "儿童",
        "孩子",
        "节能",
        "节电",
        "通风",
        "跌倒",
        "燃气",
    ]
    return _has_any(text, question_words) and _has_any(text, domain_words)


def _has_family_member(text: str, state: dict[str, Any]) -> bool:
    members = list(state.get("family", {}).get("members", {}).keys())
    aliases = ["老人", "宝宝", "小孩", "儿子", "女儿"]
    return _has_any(text, members + aliases)


def _is_profile_memory_update(text: str, state: dict[str, Any]) -> bool:
    if not _has_family_member(text, state):
        return False
    explicit_memory = _has_any(text, ["记住", "记一下", "以后记得", "长期记忆"])
    profile_words = ["喜欢", "爱吃", "不吃", "不能吃", "不喜欢", "性格", "脾气", "爱好", "偏好", "怕冷", "怕热", "睡眠浅"]
    return explicit_memory and _has_any(text, profile_words)


def _is_profile_memory_query(text: str, state: dict[str, Any]) -> bool:
    if not _has_family_member(text, state):
        return False
    query_words = [
        "你记得",
        "记得什么",
        "画像",
        "偏好",
        "爱好",
        "性格",
        "喜欢什么",
        "喜欢吃什么",
        "爱吃什么",
        "不吃什么",
    ]
    return _has_any(text, query_words)


def _extract_time(text: str) -> str | None:
    match = re.search(r"(\d{1,2})[:：点](\d{1,2})?", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        if "晚" in text and hour < 12:
            hour += 12
        return f"{hour:02d}:{minute:02d}"
    for word, value in CHINESE_NUMBERS.items():
        if f"{word}点" in text:
            hour = value
            if "晚" in text and hour < 12:
                hour += 12
            return f"{hour:02d}:00"
    return None


def _extract_retry_minutes(text: str) -> int | None:
    match = re.search(r"(\d{1,2})分钟", text)
    if match:
        return int(match.group(1))
    for word, value in CHINESE_NUMBERS.items():
        if f"{word}分钟" in text:
            return value
    return None


def _extract_reminder_id(text: str) -> str | None:
    match = re.search(r"(rem-\d{3})", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None
