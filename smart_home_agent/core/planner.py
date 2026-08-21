"""Deterministic home task planner that emits a small DAG."""

from __future__ import annotations

from typing import Any

from .models import Intent, PlanStep


class TaskPlanner:
    def build(self, intent: Intent, state: dict[str, Any], config: dict[str, Any]) -> list[PlanStep]:
        slots = intent.slots
        if intent.name == "confirmation_accept":
            pending = state.get("pending_confirmations", [])[:1]
            if not pending:
                return []
            action = pending[0]
            return [
                PlanStep(
                    step_id="s1",
                    tool=action["tool"],
                    args={**action.get("args", {}), "confirmed": True},
                    reason="执行用户已确认的敏感动作",
                )
            ]
        if intent.name == "scene_mode_apply":
            scene = slots.get("scene", "sleep")
            steps = [
                PlanStep("s1", "home_profile.query", {"target": slots.get("member_group") or slots.get("member") or "all"}, "确认目标家庭成员和房间"),
                PlanStep("s2", "scene.apply", {"scene": scene, "members": slots.get("members", [])}, "应用家庭场景模式", ["s1"]),
                PlanStep("s3", "device.query", {"device_id": "front_door_lock"}, "检查门锁状态", ["s2"]),
            ]
            if scene == "sleep":
                steps.append(PlanStep("s4", "reminder.query", {"member": "爷爷"}, "检查老人吃药提醒", ["s2"]))
            return steps
        if intent.name == "network_diagnose":
            return [
                PlanStep("s1", "home_profile.query", {"target": slots.get("member") or slots.get("room") or "主卧"}, "定位网络问题所在房间"),
                PlanStep("s2", "network.diagnose", {"room": slots.get("room"), "member": slots.get("member"), "symptom": slots.get("symptom", "network_issue"), "priority": slots.get("priority")}, "执行 Wi-Fi 质量诊断", ["s1"]),
            ]
        if intent.name == "network_apply_qos":
            return [
                PlanStep("s1", "network.apply_qos", {"room": slots.get("room"), "member": slots.get("member"), "policy": slots.get("policy", "video_call_first"), "duration_min": 60}, "根据多轮上下文开启网络优先策略")
            ]
        if intent.name == "reminder_create":
            return [
                PlanStep("s1", "reminder.create", {"member": slots.get("member") or "爷爷", "time": slots.get("time") or "21:00", "task": slots.get("task") or "吃药", "retry_after_min": slots.get("retry_after_min") or 10}, "创建老人关怀提醒")
            ]
        if intent.name == "reminder_query":
            return [PlanStep("s1", "reminder.query", {"member": slots.get("member") or "爷爷"}, "查询提醒完成状态")]
        if intent.name == "reminder_complete":
            return [
                PlanStep(
                    "s1",
                    "reminder.complete",
                    {
                        "reminder_id": slots.get("reminder_id"),
                        "member": slots.get("member") or "爷爷",
                        "task": slots.get("task"),
                        "all": bool(slots.get("all")),
                    },
                    "标记老人关怀提醒已完成",
                )
            ]
        if intent.name == "reminder_cancel":
            return [
                PlanStep(
                    "s1",
                    "reminder.cancel",
                    {
                        "reminder_id": slots.get("reminder_id"),
                        "member": slots.get("member") or "爷爷",
                        "task": slots.get("task"),
                        "all": bool(slots.get("all")),
                    },
                    "取消老人关怀提醒",
                )
            ]
        if intent.name == "knowledge_query":
            return [PlanStep("s1", "knowledge.search", {"query": slots.get("raw_text", ""), "top_k": 3}, "检索 SQLite 本地知识库")]
        if intent.name == "profile_memory_update":
            return [PlanStep("s1", "profile.remember", {"text": slots.get("raw_text", "")}, "写入长期家庭成员画像")]
        if intent.name == "profile_memory_query":
            return [PlanStep("s1", "profile.query", {"member": slots.get("member")}, "查询长期家庭成员画像")]
        if intent.name == "home_status_query":
            if slots.get("room"):
                return [
                    PlanStep("s1", "home_profile.query", {"target": slots.get("room")}, "定位目标房间和设备"),
                    PlanStep("s2", "sensor.query", {"room": slots.get("room")}, "读取该房间传感器状态", ["s1"]),
                    PlanStep("s3", "device.query", {"room": slots.get("room")}, "读取该房间设备状态", ["s1"]),
                ]
            return [
                PlanStep("s1", "home_profile.query", {"target": "all"}, "汇总家庭空间和设备"),
                PlanStep("s2", "device.query", {}, "读取全部设备状态", ["s1"]),
            ]
        if intent.name == "child_mode_apply":
            scene = slots.get("scene", "child_study")
            return [
                PlanStep("s1", "scene.apply", {"scene": scene}, "应用儿童模式场景"),
            ]
        if intent.name == "energy_query":
            return [
                PlanStep("s1", "energy.query", {"top_k": 5}, "查询家庭能耗排行"),
                PlanStep("s2", "energy.optimize", {"auto_apply": False}, "生成节能优化建议", ["s1"]),
            ]
        if intent.name == "sensor_query":
            return [PlanStep("s1", "sensor.query", {"room": slots.get("room")}, "读取传感器环境数据")]
        if intent.name == "proactive_alert":
            return [
                PlanStep("s1", "sensor.query", {}, "读取全部传感器"),
                PlanStep("s2", "sensor.check_alert", {}, "运行主动感知规则", ["s1"]),
            ]
        if intent.name == "device_control":
            args = {"room": slots.get("room"), "device": slots.get("device"), "action": slots.get("action"), "value": slots.get("value")}
            if slots.get("action") in {"unlock", "disable_camera", "cancel_alarm"}:
                return [
                    PlanStep(
                        "s1",
                        "safety.check",
                        {"device_id": slots.get("device"), "action": slots.get("action"), "pending_action": {"tool": "device.control", "args": args}},
                        "敏感设备动作进入二次确认",
                    )
                ]
            return [PlanStep("s1", "device.control", args, "执行设备控制动作")]
        return []
