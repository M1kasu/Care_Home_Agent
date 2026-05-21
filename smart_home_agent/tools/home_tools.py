"""Simulated home tools for the contest demo."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..core.models import ToolSpec
from ..memory.family_profile import FamilyProfileMemory
from ..memory.sqlite_store import SQLiteKnowledgeBase
from .registry import ToolRegistry


DEFAULT_HOME_STATE: dict[str, Any] = {
    "family": {
        "members": {
            "爷爷": {"room": "老人房", "role": "elderly", "sleep_temperature": 26},
            "奶奶": {"room": "老人房", "role": "elderly", "sleep_temperature": 26},
            "爸爸": {"room": "主卧", "role": "parent", "sleep_temperature": 25},
            "妈妈": {"room": "主卧", "role": "parent", "sleep_temperature": 25},
            "孩子": {"room": "儿童房", "role": "child", "sleep_temperature": 26},
        },
        "member_groups": {
            "爸妈": ["爸爸", "妈妈"],
            "父母": ["爸爸", "妈妈"],
            "老人": ["爷爷", "奶奶"],
        },
        "rooms": {
            "客厅": {"devices": ["livingroom_light", "livingroom_tv"], "mesh_node": "mesh_1"},
            "主卧": {"devices": ["bedroom_light", "bedroom_ac"], "mesh_node": "mesh_1"},
            "老人房": {"devices": ["elderly_room_light", "elderly_room_ac", "elderly_room_camera"], "mesh_node": "mesh_2"},
            "儿童房": {"devices": ["kids_room_light", "kids_room_ac"], "mesh_node": "mesh_2"},
            "玄关": {"devices": ["front_door_lock"], "mesh_node": "mesh_1"},
        },
    },
    "devices": {
        "livingroom_light": {"name": "客厅灯", "room": "客厅", "type": "light", "power": "on", "brightness": 80},
        "livingroom_tv": {"name": "客厅电视", "room": "客厅", "type": "tv", "power": "on"},
        "bedroom_light": {"name": "主卧灯", "room": "主卧", "type": "light", "power": "on", "brightness": 60},
        "bedroom_ac": {"name": "主卧空调", "room": "主卧", "type": "air_conditioner", "power": "on", "temperature": 26, "mode": "normal"},
        "elderly_room_light": {"name": "老人房灯", "room": "老人房", "type": "light", "power": "on", "brightness": 35},
        "elderly_room_ac": {"name": "老人房空调", "room": "老人房", "type": "air_conditioner", "power": "on", "temperature": 27, "mode": "normal"},
        "elderly_room_camera": {"name": "老人房看护摄像头", "room": "老人房", "type": "camera", "power": "on"},
        "kids_room_light": {"name": "儿童房灯", "room": "儿童房", "type": "light", "power": "off", "brightness": 0},
        "kids_room_ac": {"name": "儿童房空调", "room": "儿童房", "type": "air_conditioner", "power": "off", "temperature": 26, "mode": "eco"},
        "front_door_lock": {"name": "入户门锁", "room": "玄关", "type": "lock", "locked": True},
    },
    "network": {
        "rooms": {
            "客厅": {"rssi": -48, "latency_ms": 24, "packet_loss": 0.0, "status": "good"},
            "主卧": {"rssi": -63, "latency_ms": 42, "packet_loss": 0.01, "status": "normal"},
            "老人房": {"rssi": -72, "latency_ms": 86, "packet_loss": 0.03, "status": "warning"},
            "儿童房": {"rssi": -66, "latency_ms": 55, "packet_loss": 0.01, "status": "normal"},
        },
        "top_bandwidth_devices": [
            {"device_id": "livingroom_tv", "name": "客厅电视", "usage_mbps": 38, "priority": "normal"},
            {"device_id": "tablet_kids", "name": "儿童平板", "usage_mbps": 12, "priority": "normal"},
        ],
        "qos": [],
    },
    "reminders": [
        {"id": "rem-001", "member": "爷爷", "time": "21:00", "task": "吃降压药", "completed": False, "retry_after_min": 10},
    ],
    "sensors": {
        "客厅": {"temperature": 24.5, "humidity": 55, "motion": True, "noise_db": 35, "last_motion_min": 0},
        "主卧": {"temperature": 25.0, "humidity": 52, "motion": False, "noise_db": 28, "last_motion_min": 30},
        "老人房": {"temperature": 17.5, "humidity": 60, "motion": False, "noise_db": 20, "last_motion_min": 130},
        "儿童房": {"temperature": 25.0, "humidity": 50, "motion": True, "noise_db": 65, "last_motion_min": 0},
    },
    "energy": {
        "devices": {
            "livingroom_tv": {"power_w": 120, "standby_w": 5, "today_hours": 4.5, "today_kwh": 0.55},
            "livingroom_light": {"power_w": 18, "standby_w": 0, "today_hours": 6.0, "today_kwh": 0.11},
            "bedroom_ac": {"power_w": 800, "standby_w": 3, "today_hours": 8.0, "today_kwh": 6.40},
            "elderly_room_ac": {"power_w": 750, "standby_w": 3, "today_hours": 5.0, "today_kwh": 3.75},
            "kids_room_ac": {"power_w": 700, "standby_w": 3, "today_hours": 0.0, "today_kwh": 0.07},
            "elderly_room_light": {"power_w": 12, "standby_w": 0, "today_hours": 8.0, "today_kwh": 0.10},
        },
        "daily_kwh": 11.0,
        "threshold_kwh": 12.0,
        "price_per_kwh": 0.6,
    },
    "timers": [],
    "alerts": [],
    "pending_confirmations": [],
    "family_profiles": {},
    "history": [],
}


def ensure_home_state(state: dict[str, Any] | None) -> dict[str, Any]:
    merged = deepcopy(DEFAULT_HOME_STATE)
    if state:
        _deep_update(merged, deepcopy(state))
    merged.setdefault("session_id", (state or {}).get("session_id") or "demo-session")
    merged.setdefault("pending_confirmations", [])
    merged.setdefault("history", [])
    merged.setdefault("timers", [])
    merged.setdefault("alerts", [])
    merged.setdefault("family_profiles", {})
    return merged


def _deep_update(base: dict[str, Any], patch: dict[str, Any]) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def register_home_tools(
    registry: ToolRegistry,
    knowledge_base: SQLiteKnowledgeBase,
    profile_memory: FamilyProfileMemory | None = None,
) -> None:
    registry.register(ToolSpec("home_profile.query", "查询家庭成员、房间和设备关系"), _home_profile_query)
    registry.register(ToolSpec("device.query", "查询设备状态"), _device_query)
    registry.register(ToolSpec("device.control", "控制本地模拟设备", side_effect="write"), _device_control)
    registry.register(ToolSpec("scene.apply", "应用家庭场景模式", side_effect="write"), _scene_apply)
    registry.register(ToolSpec("network.diagnose", "诊断家庭网络质量"), _network_diagnose)
    registry.register(ToolSpec("network.apply_qos", "应用家庭网络 QoS 策略", side_effect="write"), _network_apply_qos)
    registry.register(ToolSpec("reminder.create", "创建老人关怀提醒", side_effect="write"), _reminder_create)
    registry.register(ToolSpec("reminder.query", "查询提醒状态"), _reminder_query)
    registry.register(ToolSpec("reminder.complete", "标记提醒已完成", side_effect="write"), _reminder_complete)
    registry.register(ToolSpec("reminder.cancel", "取消提醒", side_effect="write"), _reminder_cancel)
    registry.register(ToolSpec("safety.check", "敏感动作安全确认"), _safety_check)
    registry.register(ToolSpec("sensor.query", "查询房间传感器数据"), _sensor_query)
    registry.register(ToolSpec("sensor.check_alert", "检测异常传感条件并产生主动建议"), _sensor_check_alert)
    registry.register(ToolSpec("energy.query", "查询家庭能耗排行"), _energy_query)
    registry.register(ToolSpec("energy.optimize", "识别可关闭待机设备并建议节能", side_effect="write"), _energy_optimize)
    registry.register(ToolSpec("device.set_timer", "为设备设定到时关闭定时器", side_effect="write"), _device_set_timer)

    def _knowledge_search(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query") or "")
        hits = knowledge_base.search(query, top_k=int(args.get("top_k", 3)))
        message = f"本地知识库命中 {len(hits)} 条" if hits else "本地知识库未命中可信答案"
        return {"status": "success", "data": {"hits": hits}, "message": message}

    registry.register(ToolSpec("knowledge.search", "SQLite 本地知识库检索"), _knowledge_search)

    if profile_memory is not None:
        def _profile_remember(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
            state = context["state"]
            family = state.get("family", {})
            result = profile_memory.remember_from_text(
                str(args.get("text") or ""),
                known_members=list(family.get("members", {}).keys()),
                member_groups=family.get("member_groups", {}),
            )
            state["family_profiles"] = result["profiles"]
            status = "success" if result.get("updated") else "error"
            return {"status": status, "data": result, "message": result["message"]}

        def _profile_query(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
            state = context["state"]
            member = args.get("member")
            result = profile_memory.query(str(member) if member else None)
            state["family_profiles"] = profile_memory.load()
            return {"status": "success", "data": result, "message": result["message"]}

        registry.register(ToolSpec("profile.remember", "写入长期家庭成员画像", side_effect="write"), _profile_remember)
        registry.register(ToolSpec("profile.query", "查询长期家庭成员画像"), _profile_query)


def _home_profile_query(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    family = state["family"]
    target = args.get("target") or args.get("member") or args.get("room") or "all"
    members = _resolve_members(target, family)
    rooms = []
    for member in members:
        room = family["members"].get(member, {}).get("room")
        if room and room not in rooms:
            rooms.append(room)
    if target in family["rooms"] and target not in rooms:
        rooms.append(target)
    if target == "all":
        rooms = list(family["rooms"].keys())
    devices = []
    for room in rooms:
        devices.extend(family["rooms"].get(room, {}).get("devices", []))
    return {
        "status": "success",
        "data": {"target": target, "members": members, "rooms": rooms, "devices": devices},
        "message": "家庭档案查询完成",
    }


def _device_query(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    device_id = args.get("device_id")
    if device_id:
        device = state["devices"].get(device_id)
        if not device:
            return {"status": "error", "message": f"未找到设备 {device_id}"}
        return {"status": "success", "data": {"device_id": device_id, "state": deepcopy(device)}, "message": f"{device['name']} 状态已读取"}
    room = args.get("room")
    devices = {
        did: deepcopy(device)
        for did, device in state["devices"].items()
        if room is None or device.get("room") == room
    }
    return {"status": "success", "data": {"devices": devices}, "message": "设备状态已读取"}


def _device_control(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    device_id = args.get("device_id") or _find_device_id(state, args.get("device"), args.get("room"))
    if not device_id or device_id not in state["devices"]:
        return {"status": "error", "message": "未找到可控制设备"}
    device = state["devices"][device_id]
    old_state = deepcopy(device)
    action = args.get("action")
    value = args.get("value")
    if action == "turn_on":
        device["power"] = "on"
        if device.get("type") == "light" and device.get("brightness", 0) == 0:
            device["brightness"] = 60
    elif action == "turn_off":
        device["power"] = "off"
        if device.get("type") == "light":
            device["brightness"] = 0
    elif action == "set_brightness":
        device["power"] = "on"
        device["brightness"] = int(value)
    elif action == "set_temperature":
        device["power"] = "on"
        device["temperature"] = int(value)
    elif action == "set_mode":
        device["power"] = "on"
        device["mode"] = str(value)
    elif action == "lock":
        device["locked"] = True
    elif action == "unlock":
        device["locked"] = False
    else:
        return {"status": "error", "message": f"不支持的设备动作: {action}"}
    return {
        "status": "success",
        "data": {"device_id": device_id, "old_state": old_state, "new_state": deepcopy(device)},
        "message": f"{device['name']} 已执行 {action}",
    }


def _scene_apply(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    scene = args.get("scene", "sleep")
    actions: list[dict[str, Any]] = []
    if scene == "sleep":
        actions.extend(
            [
                _apply_device(state, "livingroom_tv", "turn_off"),
                _apply_device(state, "livingroom_light", "set_brightness", 20),
                _apply_device(state, "bedroom_ac", "set_mode", "sleep"),
                _apply_device(state, "elderly_room_light", "set_brightness", 10),
            ]
        )
        state["active_scene"] = "sleep"
        message = "睡前模式已应用"
    elif scene == "away":
        actions.extend(
            [
                _apply_device(state, "livingroom_tv", "turn_off"),
                _apply_device(state, "livingroom_light", "turn_off"),
                _apply_device(state, "bedroom_light", "turn_off"),
                _apply_device(state, "front_door_lock", "lock"),
            ]
        )
        state["active_scene"] = "away"
        message = "离家模式已应用"
    elif scene == "movie":
        actions.extend([
            _apply_device(state, "livingroom_tv", "turn_on"),
            _apply_device(state, "livingroom_light", "set_brightness", 15),
        ])
        state["active_scene"] = "movie"
        message = "观影模式已应用"
    elif scene == "child_study":
        actions.extend([
            _apply_device(state, "kids_room_light", "set_brightness", 75),
            _apply_device(state, "kids_room_ac", "set_temperature", 25),
        ])
        timer = _add_timer(state, "kids_room_light", action="turn_off", minutes=45, reason="儿童护眼休息提醒")
        actions.append({"device_id": "kids_room_light", "action": "set_timer", "minutes": 45, "timer_id": timer["id"]})
        state["active_scene"] = "child_study"
        message = "儿童学习模式已应用，45 分钟后会提醒护眼休息"
    elif scene == "child_sleep":
        actions.extend([
            _apply_device(state, "kids_room_light", "set_brightness", 8),
            _apply_device(state, "kids_room_ac", "set_mode", "sleep"),
            _apply_device(state, "kids_room_ac", "set_temperature", 26),
        ])
        # 强制关闭儿童房电视/平板（如存在）
        for dev_id, dev in state["devices"].items():
            if dev.get("room") == "儿童房" and dev.get("type") in {"tv", "tablet"} and dev.get("power") == "on":
                actions.append(_apply_device(state, dev_id, "turn_off"))
        state["active_scene"] = "child_sleep"
        message = "儿童睡眠模式已应用，护眼夜灯已开启"
    else:
        message = f"场景 {scene} 暂未配置，未执行动作"
    return {"status": "success", "data": {"scene": scene, "actions": actions}, "message": message}


def _network_diagnose(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    room = args.get("room") or _room_for_member(state, args.get("member")) or state.get("last_room") or "主卧"
    room_metric = deepcopy(state["network"]["rooms"].get(room, state["network"]["rooms"]["主卧"]))
    suggestions = []
    if room_metric["rssi"] <= -68:
        suggestions.append("Mesh 信号偏弱，建议切换到更近节点或调整节点位置")
    if room_metric["latency_ms"] >= 70 or room_metric["packet_loss"] >= 0.02:
        suggestions.append("检测到延迟或丢包偏高，可临时开启视频通话 QoS")
    if state["network"].get("top_bandwidth_devices"):
        suggestions.append("客厅电视占用较高带宽，可降低其优先级")
    diagnosis = "；".join(suggestions) if suggestions else "网络状态正常，未发现明显异常"
    state["last_room"] = room
    state["last_task"] = {"intent": "network_diagnose", "room": room}
    return {
        "status": "success",
        "data": {
            "room": room,
            **room_metric,
            "top_bandwidth_devices": deepcopy(state["network"].get("top_bandwidth_devices", [])),
            "diagnosis": diagnosis,
            "suggestions": suggestions,
        },
        "message": f"{room} 网络诊断完成",
    }


def _network_apply_qos(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    room = args.get("room") or state.get("last_room") or _room_for_member(state, args.get("member")) or "老人房"
    policy = {"room": room, "policy": args.get("policy", "video_call_first"), "duration_min": int(args.get("duration_min", 60))}
    state["network"].setdefault("qos", []).append(policy)
    if room in state["network"]["rooms"]:
        state["network"]["rooms"][room]["status"] = "optimized"
        state["network"]["rooms"][room]["latency_ms"] = max(30, state["network"]["rooms"][room]["latency_ms"] - 28)
        state["network"]["rooms"][room]["packet_loss"] = 0.005
    for item in state["network"].get("top_bandwidth_devices", []):
        if item.get("device_id") == "livingroom_tv":
            item["priority"] = "low"
    state["last_task"] = {"intent": "network_apply_qos", "room": room}
    return {"status": "success", "data": policy, "message": f"已开启{room}视频优先策略"}


def _reminder_create(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    reminder = {
        "id": f"rem-{len(state['reminders']) + 1:03d}",
        "member": args.get("member") or "爷爷",
        "time": args.get("time") or "21:00",
        "task": args.get("task") or "吃药",
        "completed": False,
        "canceled": False,
        "retry_after_min": int(args.get("retry_after_min") or 10),
    }
    state["reminders"].append(reminder)
    return {"status": "success", "data": {"reminder": deepcopy(reminder)}, "message": "关怀提醒已创建"}


def _reminder_query(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    member = args.get("member")
    reminders = [item for item in state["reminders"] if member is None or item.get("member") == member]
    return {"status": "success", "data": {"reminders": deepcopy(reminders)}, "message": "提醒状态已查询"}


def _reminder_complete(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    matches = _select_reminders(state, args, pending_only=True)
    if not matches:
        return {"status": "error", "data": {"updated": []}, "message": "没有找到可标记完成的待办提醒"}
    if not args.get("all"):
        matches = matches[:1]
    updated = []
    for reminder in matches:
        reminder["completed"] = True
        reminder["canceled"] = False
        reminder["completed_at"] = "now"
        updated.append(deepcopy(reminder))
    return {
        "status": "success",
        "data": {"updated": updated},
        "message": f"已标记 {len(updated)} 条提醒为完成",
    }


def _reminder_cancel(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    matches = [item for item in _select_reminders(state, args, pending_only=False) if not item.get("canceled")]
    if not matches:
        return {"status": "error", "data": {"updated": []}, "message": "没有找到可取消的提醒"}
    if not args.get("all"):
        matches = matches[:1]
    updated = []
    for reminder in matches:
        reminder["canceled"] = True
        reminder["canceled_at"] = "now"
        updated.append(deepcopy(reminder))
    return {
        "status": "success",
        "data": {"updated": updated},
        "message": f"已取消 {len(updated)} 条提醒",
    }


def _safety_check(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    action = args.get("action")
    device_id = args.get("device_id")
    sensitive = action in {"unlock", "disable_camera", "cancel_alarm"}
    if sensitive:
        pending = args.get("pending_action") or {}
        return {
            "status": "blocked",
            "data": {"need_confirmation": True, "pending_action": pending},
            "message": f"{device_id or '该设备'} 的 {action} 属于敏感动作，需要二次确认",
        }
    return {"status": "success", "data": {"need_confirmation": False}, "message": "安全检查通过"}


def _select_reminders(state: dict[str, Any], args: dict[str, Any], *, pending_only: bool) -> list[dict[str, Any]]:
    reminder_id = args.get("reminder_id")
    member = args.get("member")
    task = args.get("task")
    matches = []
    for reminder in state.get("reminders", []):
        if reminder_id and reminder.get("id") != reminder_id:
            continue
        if member and reminder.get("member") != member:
            continue
        reminder_task = str(reminder.get("task", ""))
        if task and task not in reminder_task and not ("药" in str(task) and "药" in reminder_task):
            continue
        if pending_only and (reminder.get("completed") or reminder.get("canceled")):
            continue
        matches.append(reminder)
    return matches


def _resolve_members(target: Any, family: dict[str, Any]) -> list[str]:
    if isinstance(target, list):
        members: list[str] = []
        for item in target:
            members.extend(_resolve_members(item, family))
        return list(dict.fromkeys(members))
    text = str(target)
    if text in family["member_groups"]:
        return family["member_groups"][text]
    return [name for name in family["members"] if name in text]


def _room_for_member(state: dict[str, Any], member: Any) -> str | None:
    if not member:
        return None
    members = _resolve_members(member, state["family"])
    if not members:
        return None
    return state["family"]["members"].get(members[0], {}).get("room")


def _find_device_id(state: dict[str, Any], device: Any, room: Any) -> str | None:
    device_text = str(device or "")
    room_text = str(room or "")
    type_map = {"灯": "light", "空调": "air_conditioner", "电视": "tv", "门锁": "lock", "锁": "lock", "摄像头": "camera"}
    target_type = next((value for key, value in type_map.items() if key in device_text), None)
    for device_id, info in state["devices"].items():
        if target_type and info.get("type") != target_type:
            continue
        if room_text and info.get("room") != room_text:
            continue
        return device_id
    return None


def _apply_device(state: dict[str, Any], device_id: str, action: str, value: Any = None) -> dict[str, Any]:
    result = _device_control({"device_id": device_id, "action": action, "value": value}, {"state": state})
    return {"device_id": device_id, "action": action, "value": value, "result": result.get("status"), "message": result.get("message")}


# ---------------------------------------------------------------------------
# Sensor / Energy / Timer tools
# ---------------------------------------------------------------------------


def _sensor_query(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    room = args.get("room")
    sensors = state.get("sensors", {})
    if room:
        info = sensors.get(room)
        if not info:
            return {"status": "error", "message": f"未找到房间 {room} 的传感器"}
        return {"status": "success", "data": {"room": room, "sensor": deepcopy(info)}, "message": f"{room} 传感器已读取"}
    return {"status": "success", "data": {"sensors": deepcopy(sensors)}, "message": "传感器全量已读取"}


def _sensor_check_alert(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    sensors = state.get("sensors", {})
    alerts: list[dict[str, Any]] = []
    elderly = sensors.get("老人房", {})
    if elderly.get("last_motion_min", 0) >= 120 and not elderly.get("motion"):
        alerts.append({
            "level": "warning",
            "room": "老人房",
            "type": "no_motion",
            "message": f"老人房已 {elderly.get('last_motion_min')} 分钟无活动，建议查看摄像头或拨打电话",
        })
    if elderly.get("temperature", 99) < 18:
        alerts.append({
            "level": "info",
            "room": "老人房",
            "type": "cold",
            "message": f"老人房温度仅 {elderly.get('temperature')}℃，建议开启空调制暖到 24℃",
            "suggested_action": {"tool": "device.control", "args": {"device_id": "elderly_room_ac", "action": "set_temperature", "value": 24}},
        })
    kids = sensors.get("儿童房", {})
    hour = int(args.get("hour", 22))
    if kids.get("noise_db", 0) > 60 and hour >= 22:
        alerts.append({
            "level": "info",
            "room": "儿童房",
            "type": "late_noise",
            "message": f"儿童房当前噪声 {kids.get('noise_db')}dB 且已过睡觉时间，建议切到儿童睡眠模式",
            "suggested_action": {"tool": "scene.apply", "args": {"scene": "child_sleep"}},
        })
    state["alerts"] = alerts
    return {"status": "success", "data": {"alerts": alerts}, "message": f"主动感知发现 {len(alerts)} 条建议"}


def _energy_query(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    energy = state.get("energy", {})
    devices_info = energy.get("devices", {})
    ranking = sorted(
        (
            {
                "device_id": did,
                "name": state["devices"].get(did, {}).get("name", did),
                **deepcopy(info),
            }
            for did, info in devices_info.items()
        ),
        key=lambda item: item.get("today_kwh", 0),
        reverse=True,
    )
    daily_kwh = energy.get("daily_kwh", 0)
    threshold = energy.get("threshold_kwh", 0)
    over = daily_kwh > threshold
    return {
        "status": "success",
        "data": {
            "daily_kwh": daily_kwh,
            "threshold_kwh": threshold,
            "price_per_kwh": energy.get("price_per_kwh", 0),
            "estimated_cost": round(daily_kwh * energy.get("price_per_kwh", 0), 2),
            "over_threshold": over,
            "ranking": ranking[: int(args.get("top_k", 5))],
        },
        "message": f"今日能耗 {daily_kwh} kWh" + ("，已超阈值" if over else "，处于正常范围"),
    }


def _energy_optimize(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    energy_devices = state.get("energy", {}).get("devices", {})
    suggestions: list[dict[str, Any]] = []
    for did, info in energy_devices.items():
        device = state["devices"].get(did, {})
        # 待机但仍开启
        if device.get("power") == "on" and info.get("today_hours", 0) == 0:
            suggestions.append({
                "device_id": did,
                "name": device.get("name", did),
                "reason": "今日未使用但仍处于开启/待机状态",
                "action": {"tool": "device.control", "args": {"device_id": did, "action": "turn_off"}},
                "saving_kwh_per_day": round(info.get("standby_w", 0) * 24 / 1000, 2),
            })
    # 高能耗设备建议
    top = sorted(energy_devices.items(), key=lambda kv: kv[1].get("today_kwh", 0), reverse=True)
    if top and top[0][1].get("today_kwh", 0) > 5:
        did, info = top[0]
        suggestions.append({
            "device_id": did,
            "name": state["devices"].get(did, {}).get("name", did),
            "reason": f"今日已耗 {info['today_kwh']} kWh，建议在睡眠时段切换到 ECO 模式",
            "action": {"tool": "device.control", "args": {"device_id": did, "action": "set_mode", "value": "eco"}},
            "saving_kwh_per_day": round(info.get("today_kwh", 0) * 0.2, 2),
        })
    auto_apply = bool(args.get("auto_apply"))
    applied: list[dict[str, Any]] = []
    if auto_apply:
        for sug in suggestions:
            tool_args = sug["action"]["args"]
            applied.append(_device_control(tool_args, {"state": state}))
    return {
        "status": "success",
        "data": {"suggestions": suggestions, "applied": applied},
        "message": f"识别出 {len(suggestions)} 项节能建议" + ("，已自动执行" if auto_apply else ""),
    }


def _device_set_timer(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    state = context["state"]
    device_id = args.get("device_id") or _find_device_id(state, args.get("device"), args.get("room"))
    if not device_id or device_id not in state["devices"]:
        return {"status": "error", "message": "未找到可设定的设备"}
    minutes = int(args.get("minutes") or 30)
    action = str(args.get("action") or "turn_off")
    timer = _add_timer(state, device_id, action=action, minutes=minutes, reason=str(args.get("reason") or ""))
    return {
        "status": "success",
        "data": {"timer": timer},
        "message": f"{state['devices'][device_id]['name']} 已设定 {minutes} 分钟后 {action}",
    }


def _add_timer(state: dict[str, Any], device_id: str, *, action: str, minutes: int, reason: str = "") -> dict[str, Any]:
    timers = state.setdefault("timers", [])
    timer = {
        "id": f"timer-{len(timers) + 1:03d}",
        "device_id": device_id,
        "action": action,
        "minutes": minutes,
        "reason": reason,
    }
    timers.append(timer)
    return timer
