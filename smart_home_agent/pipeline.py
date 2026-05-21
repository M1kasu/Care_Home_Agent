"""Main smart-home agent pipeline."""

from __future__ import annotations

import time
from typing import Any

from .core.executor import PlanExecutor
from .core.models import Intent, ToolResult
from .core.planner import TaskPlanner
from .core.router import LocalRouter
from .memory.family_profile import FamilyProfileMemory
from .memory.session import SessionMemory
from .memory.sqlite_store import SQLiteKnowledgeBase
from .providers.local_llm import get_cached_local_llm_client
from .settings import merge_config
from .tools.home_tools import ensure_home_state, register_home_tools
from .tools.registry import ToolRegistry


class SmartHomeAgent:
    def __init__(self) -> None:
        self.memory = SessionMemory(max_items=12)
        self.router = LocalRouter(self.memory)
        self.planner = TaskPlanner()
        self.registry = ToolRegistry()
        self._knowledge: SQLiteKnowledgeBase | None = None
        self._profile_memory: FamilyProfileMemory | None = None
        self._sqlite_path: str | None = None
        self.executor = PlanExecutor(self.registry)

    def run(self, user_input: str, state: dict | None = None, config: dict | None = None) -> dict:
        total_start = time.perf_counter()
        cfg = merge_config(config)
        self._ensure_tools(cfg)
        working_state = ensure_home_state(state)
        if self._profile_memory is not None:
            self._profile_memory.apply_to_state(working_state)
        user_input = str(user_input or "").strip()
        if not user_input:
            user_input = "家里现在状态怎么样？"
        intent, nlu_metrics = self.router.route(user_input, working_state, cfg)
        if intent.name == "confirmation_reject":
            working_state["pending_confirmations"] = []
            reply = "已取消待确认动作，没有执行敏感设备控制。"
            plan = []
            tool_results: list[ToolResult] = []
            safety = {"need_confirmation": False, "message": ""}
        else:
            plan = self.planner.build(intent, working_state, cfg)
            tool_results, safety = self.executor.execute(plan, {"state": working_state}, cfg)
            if intent.name == "confirmation_accept":
                working_state["pending_confirmations"] = []
            reply = self._reply(intent, tool_results, safety, working_state)
            if (
                intent.name == "unknown"
                or self._should_fallback_to_direct_reply(intent, plan, tool_results, cfg)
            ):
                reply, reply_metrics = self._llm_direct_reply(user_input, working_state, cfg)
                nlu_metrics.update(reply_metrics)

        working_state["last_intent"] = intent.name
        working_state["last_slots"] = intent.slots
        self.memory.append(working_state, role="user", content=user_input, intent=intent.name)
        self.memory.append(working_state, role="assistant", content=reply, intent=intent.name)

        total_latency_ms = int((time.perf_counter() - total_start) * 1000)
        tool_latency_ms = sum(item.duration_ms for item in tool_results)
        metrics = {
            "total_latency_ms": total_latency_ms,
            "nlu_latency_ms": nlu_metrics.get("nlu_latency_ms", 0),
            "model_latency_ms": nlu_metrics.get("model_latency_ms", 0) + nlu_metrics.get("answer_model_latency_ms", 0),
            "model_attempted": bool(nlu_metrics.get("model_attempted", False) or nlu_metrics.get("answer_model_attempted", False)),
            "model_available": bool(nlu_metrics.get("model_available", False) or nlu_metrics.get("answer_model_available", False)),
            "model_error": nlu_metrics.get("model_error", "") or nlu_metrics.get("answer_model_error", ""),
            "model_raw_output": nlu_metrics.get("model_raw_output", ""),
            "model_cache_hit": bool(nlu_metrics.get("model_cache_hit", False)),
            "answer_model_attempted": bool(nlu_metrics.get("answer_model_attempted", False)),
            "answer_model_available": bool(nlu_metrics.get("answer_model_available", False)),
            "answer_model_latency_ms": nlu_metrics.get("answer_model_latency_ms", 0),
            "answer_model_error": nlu_metrics.get("answer_model_error", ""),
            "answer_model_raw_output": nlu_metrics.get("answer_model_raw_output", ""),
            "planning_latency_ms": max(1, total_latency_ms - nlu_metrics.get("nlu_latency_ms", 0) - tool_latency_ms),
            "tool_latency_ms": tool_latency_ms,
            "memory_mb": self._estimate_memory_mb(working_state),
        }
        return {
            "reply": reply,
            "intent": intent.to_dict(),
            "plan": [step.to_dict() for step in plan],
            "tool_results": [item.to_dict() for item in tool_results],
            "state": working_state,
            "metrics": metrics,
            "safety": safety,
        }

    def _ensure_tools(self, config: dict[str, Any]) -> None:
        sqlite_path = str(config.get("sqlite_path") or "")
        if self._knowledge is not None and self._profile_memory is not None and self._sqlite_path == sqlite_path:
            return
        self.registry = ToolRegistry()
        self.executor = PlanExecutor(self.registry)
        embedder = None
        if config.get("enable_embedding_search") and config.get("enable_local_llm"):
            from .providers.local_llm import LocalLLMClient

            client = LocalLLMClient(
                model_path=config["model_path"],
                n_ctx=int(config.get("n_ctx", 1024)),
                n_threads=int(config.get("n_threads", 4)),
            )
            embedder = client.embed
        self._knowledge = SQLiteKnowledgeBase(config.get("sqlite_path"), embedder=embedder)
        self._profile_memory = FamilyProfileMemory(config.get("sqlite_path"))
        self._sqlite_path = sqlite_path
        register_home_tools(self.registry, self._knowledge, self._profile_memory)

    @staticmethod
    def _should_fallback_to_direct_reply(
        intent: Intent,
        plan: list[Any],
        tool_results: list[ToolResult],
        config: dict[str, Any],
    ) -> bool:
        if not config.get("enable_local_llm"):
            return False
        if intent.name == "knowledge_query":
            result = _find_result(tool_results, "knowledge.search")
            hits = result.data.get("hits", []) if result else []
            return not hits
        if intent.name != "unknown" and not plan:
            return True
        return False

    def _llm_direct_reply(
        self,
        user_input: str,
        state: dict[str, Any],
        config: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        metrics: dict[str, Any] = {
            "answer_model_attempted": False,
            "answer_model_available": False,
            "answer_model_latency_ms": 0,
            "answer_model_error": "",
            "answer_model_raw_output": "",
        }
        if not config.get("enable_local_llm"):
            return self._default_unknown_reply(), metrics

        client = get_cached_local_llm_client(config)
        prompt = self._build_direct_reply_prompt(user_input, state)
        start = time.perf_counter()
        raw = client.generate_reply(prompt)
        metrics["answer_model_latency_ms"] = int((time.perf_counter() - start) * 1000)
        status = client.status()
        metrics["answer_model_attempted"] = True
        metrics["answer_model_available"] = bool(status.get("available"))
        metrics["answer_model_error"] = str(status.get("load_error") or "")
        metrics["answer_model_raw_output"] = raw or ""
        if raw:
            return raw.strip(), metrics
        return self._default_unknown_reply(), metrics

    @staticmethod
    def _build_direct_reply_prompt(user_input: str, state: dict[str, Any]) -> str:
        sensors = state.get("sensors", {})
        sensor_text = "；".join(
            f"{room}: {info.get('temperature')}℃, 湿度{info.get('humidity')}%, "
            f"{'有人活动' if info.get('motion') else str(info.get('last_motion_min', 0)) + '分钟无活动'}"
            for room, info in sensors.items()
        )
        history_text = SmartHomeAgent._recent_history_text(state)
        profile_text = SmartHomeAgent._family_profile_text(state)
        capabilities = "睡前场景联动、老人关怀提醒、家庭网络诊断与 QoS、主动巡检、安全确认、传感器查询"
        return (
            "<|im_start|>system\n"
            "你是“兴享智家”的端侧家庭中枢助手，定位是三代同堂家庭的本地家庭中枢。"
            "当用户问题没有匹配到确定任务意图，或本地知识库没有可信命中时，你可以直接回答普通生活问题，但必须遵守："
            "1) 必须阅读最近对话，遇到“什么步骤、继续、然后呢、它呢”等追问时承接上一轮话题；"
            "2) 对做菜、吃什么、生活建议这类低风险问题可以直接给建议；"
            "3) 如果用户问饮食、活动、提醒或照护建议，优先参考长期家庭画像；"
            "4) 不编造外部实时信息、医疗诊断或数据库里不存在的家庭规则；"
            "5) 如果问题需要联网或权威来源，说明本地端侧无法确认，并给出可执行替代建议；"
            "6) 回复用中文，简短但完整；需要步骤时用编号列表，最多 6 步。\n"
            f"系统能力：{capabilities}\n"
            f"当前本地传感器：{sensor_text}\n"
            f"长期家庭画像：\n{profile_text or '无'}\n"
            f"最近对话：\n{history_text or '无'}\n"
            "<|im_end|>\n"
            f"<|im_start|>user\n{user_input}\n<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

    @staticmethod
    def _recent_history_text(state: dict[str, Any], limit: int = 6) -> str:
        role_names = {"user": "用户", "assistant": "助手"}
        recent = state.get("history", [])[-limit:]
        lines = []
        for item in recent:
            role = role_names.get(str(item.get("role")), str(item.get("role") or "unknown"))
            content = str(item.get("content") or "").strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    @staticmethod
    def _family_profile_text(state: dict[str, Any]) -> str:
        profiles = state.get("family_profiles", {})
        lines = []
        for member, profile in profiles.items():
            parts = []
            if profile.get("personality"):
                parts.append("性格=" + "、".join(profile["personality"]))
            if profile.get("hobbies"):
                parts.append("爱好=" + "、".join(profile["hobbies"]))
            if profile.get("diet"):
                parts.append("饮食=" + "、".join(profile["diet"]))
            if profile.get("notes"):
                parts.append("备注=" + "、".join(profile["notes"]))
            if parts:
                lines.append(f"{member}: " + "；".join(parts))
        return "\n".join(lines)

    @staticmethod
    def _default_unknown_reply() -> str:
        return "我还没识别出明确的家庭任务。你可以换个说法，或者直接问我睡前模式、老人关怀、网络诊断、主动巡检和设备控制。"

    def _reply(
        self,
        intent: Intent,
        tool_results: list[ToolResult],
        safety: dict[str, Any],
        state: dict[str, Any],
    ) -> str:
        if safety.get("need_confirmation"):
            return f"{safety.get('message')}。请回复“确认执行”继续，或回复“取消”。"
        if intent.name == "scene_mode_apply":
            scene_result = _find_result(tool_results, "scene.apply")
            lock_result = _find_result(tool_results, "device.query")
            reminder_result = _find_result(tool_results, "reminder.query")
            parts = [scene_result.message or "场景模式已处理"]
            if lock_result and lock_result.status == "success":
                locked = lock_result.data.get("state", {}).get("locked")
                parts.append("门锁已上锁" if locked else "门锁未上锁")
            if reminder_result and reminder_result.status == "success":
                unfinished = [item for item in reminder_result.data.get("reminders", []) if not item.get("completed")]
                if unfinished:
                    parts.append(f"仍有 {len(unfinished)} 条老人关怀提醒未完成")
            return "，".join(parts) + "。"
        if intent.name == "network_diagnose":
            result = _find_result(tool_results, "network.diagnose")
            if not result:
                return "未能完成网络诊断。"
            data = result.data
            return (
                f"{data.get('room')} 网络诊断完成：RSSI {data.get('rssi')} dBm，"
                f"延迟 {data.get('latency_ms')} ms，丢包率 {data.get('packet_loss'):.1%}。"
                f"{data.get('diagnosis')}。是否要临时开启该房间视频优先？"
            )
        if intent.name == "network_apply_qos":
            result = _find_result(tool_results, "network.apply_qos")
            return (result.message if result else "已处理网络优先策略") + "，持续 60 分钟。"
        if intent.name == "reminder_create":
            result = _find_result(tool_results, "reminder.create")
            reminder = (result.data or {}).get("reminder", {}) if result else {}
            return f"已创建{reminder.get('member', '家人')} {reminder.get('time', '指定时间')} 的{reminder.get('task', '提醒')}，未回应会在 {reminder.get('retry_after_min', 10)} 分钟后再次提醒。"
        if intent.name == "reminder_query":
            result = _find_result(tool_results, "reminder.query")
            reminders = result.data.get("reminders", []) if result else []
            if not reminders:
                return "没有查到相关提醒。"
            active = [item for item in reminders if not item.get("canceled")]
            unfinished = [item for item in active if not item.get("completed")]
            completed = [item for item in active if item.get("completed")]
            canceled = [item for item in reminders if item.get("canceled")]
            return f"查到 {len(reminders)} 条提醒：{len(unfinished)} 条待完成，{len(completed)} 条已完成，{len(canceled)} 条已取消。"
        if intent.name == "reminder_complete":
            result = _find_result(tool_results, "reminder.complete")
            if not result or result.status != "success":
                return (result.message if result else "没有找到可完成的提醒") + "。"
            updated = result.data.get("updated", [])
            detail = "、".join(f"{item.get('member')} {item.get('time')} {item.get('task')}" for item in updated)
            return f"已完成提醒：{detail or result.message}。"
        if intent.name == "reminder_cancel":
            result = _find_result(tool_results, "reminder.cancel")
            if not result or result.status != "success":
                return (result.message if result else "没有找到可取消的提醒") + "。"
            updated = result.data.get("updated", [])
            detail = "、".join(f"{item.get('member')} {item.get('time')} {item.get('task')}" for item in updated)
            return f"已取消提醒：{detail or result.message}。"
        if intent.name == "knowledge_query":
            result = _find_result(tool_results, "knowledge.search")
            hits = result.data.get("hits", []) if result else []
            if not hits:
                return "本地知识库没有找到可引用的明确答案，我不会编造结论；可以补充家庭规则后再查询。"
            top = hits[0]
            source = top.get("source", "local")
            score = top.get("score")
            return f"根据本地知识库《{top['title']}》（{source}，score={score}）：{top['content']}"
        if intent.name == "profile_memory_update":
            result = _find_result(tool_results, "profile.remember")
            return (result.message if result else "已更新长期家庭画像") + "。"
        if intent.name == "profile_memory_query":
            result = _find_result(tool_results, "profile.query")
            return (result.message if result else "还没有长期家庭画像") + "。"
        if intent.name == "device_control" or intent.name == "confirmation_accept":
            result = _find_result(tool_results, "device.control")
            return (result.message if result else "设备动作已处理") + "。"
        if intent.name == "home_status_query":
            sensor_result = _find_result(tool_results, "sensor.query")
            if sensor_result and sensor_result.status == "success":
                data = sensor_result.data
                room = data.get("room") or intent.slots.get("room")
                sensor = data.get("sensor", {})
                if sensor.get("motion"):
                    activity = "有人活动"
                else:
                    activity = f"已 {sensor.get('last_motion_min')} 分钟无人活动"
                device_result = _find_result(tool_results, "device.query")
                devices = device_result.data.get("devices", {}) if device_result else {}
                on_devices = [info.get("name") for info in devices.values() if info.get("power") == "on"]
                device_text = f"开启中的设备包括：{'、'.join(on_devices)}" if on_devices else "当前没有开启中的模拟设备"
                return (
                    f"{room} 当前温度 {sensor.get('temperature')}℃，湿度 {sensor.get('humidity')}%，"
                    f"{activity}；{device_text}。"
                )
            device_result = _find_result(tool_results, "device.query")
            devices = device_result.data.get("devices", {}) if device_result else state.get("devices", {})
            on_devices = [info.get("name") for info in devices.values() if info.get("power") == "on"]
            return f"当前家中共有 {len(devices)} 个模拟设备，开启中的设备包括：{'、'.join(on_devices[:6]) or '暂无'}。"
        if intent.name == "child_mode_apply":
            scene_result = _find_result(tool_results, "scene.apply")
            timer_result = _find_result(tool_results, "device.set_timer")
            parts = [scene_result.message if scene_result else "儿童模式已处理"]
            if timer_result and timer_result.status == "success":
                parts.append(timer_result.message)
            return "，".join(parts) + "。"
        if intent.name == "energy_query":
            q = _find_result(tool_results, "energy.query")
            o = _find_result(tool_results, "energy.optimize")
            if not q:
                return "未能查询到能耗数据。"
            data = q.data
            top = data.get("ranking", [])[:3]
            top_text = "、".join(f"{i['name']}({i.get('today_kwh', 0)}kWh)" for i in top) or "暂无"
            tail = ""
            if o and o.data.get("suggestions"):
                tail = f" 节能建议：{o.data['suggestions'][0]['name']}-{o.data['suggestions'][0]['reason']}。"
            return (
                f"今日总能耗 {data.get('daily_kwh')} kWh，预计电费 ¥{data.get('estimated_cost')}，"
                f"耗电 Top3：{top_text}。"
                + (" 已超出每日阈值。" if data.get("over_threshold") else "")
                + tail
            )
        if intent.name == "sensor_query":
            r = _find_result(tool_results, "sensor.query")
            if not r:
                return "未能读取传感器数据。"
            data = r.data
            if "sensor" in data:
                s = data["sensor"]
                if s.get("motion"):
                    activity = "有人活动"
                else:
                    activity = f"已 {s.get('last_motion_min')} 分钟无人活动"
                return f"{data['room']} 当前温度 {s.get('temperature')}℃，湿度 {s.get('humidity')}%，{activity}。"
            sensors = data.get("sensors", {})
            return "全屋环境：" + "；".join(
                f"{room} {info.get('temperature')}℃/{info.get('humidity')}%" for room, info in sensors.items()
            )
        if intent.name == "proactive_alert":
            r = _find_result(tool_results, "sensor.check_alert")
            alerts = r.data.get("alerts", []) if r else []
            if not alerts:
                return "已巡检全屋传感器，未发现明显异常。"
            lines = [f"主动感知发现 {len(alerts)} 条建议："]
            for a in alerts:
                lines.append(f"• [{a['level']}] {a['message']}")
            return "\n".join(lines)
        return "我可以处理睡前模式、网络诊断、老人提醒、设备控制和本地知识问答。"

    @staticmethod
    def _estimate_memory_mb(state: dict[str, Any]) -> int:
        rough_state_kb = len(str(state).encode("utf-8")) // 1024
        return 72 + min(64, rough_state_kb // 8)


def _find_result(results: list[ToolResult], tool_name: str) -> ToolResult | None:
    for result in results:
        if result.tool == tool_name:
            return result
    return None
