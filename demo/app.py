"""兴享智家·慧家中枢 — Gradio Web 演示界面。

启动方式：
    pip install gradio
    python demo/app.py

界面布局（四区）：
    左侧 → 对话区 + 快捷场景按钮
    右侧 → 任务规划/工具日志、设备状态面板
    底部 → 性能指标
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import run  # noqa: E402
from smart_home_agent.memory.family_profile import FamilyProfileMemory  # noqa: E402
from smart_home_agent.providers.local_llm import get_cached_local_llm_client  # noqa: E402
from smart_home_agent.settings import DEFAULT_CONFIG  # noqa: E402

try:
    import gradio as gr
except ImportError as exc:  # pragma: no cover - 仅在缺依赖时
    raise SystemExit(
        "未检测到 gradio，请先执行: pip install gradio>=4.0"
    ) from exc


SHORTCUTS = [
    ("睡前模式", "爸妈准备睡了，帮我切到睡前模式，顺便检查一下门锁。"),
    ("离家模式", "我们要出门了，切离家模式并锁门。"),
    ("观影模式", "晚上看电影，帮我准备一下客厅。"),
    ("网络诊断", "爷爷房间视频有点卡，帮我看看。"),
    ("老人巡检", "看看老人房现在怎么样？"),
    ("一键巡检", "一键巡检家里有没有异常。"),
    ("儿童学习", "给孩子开学习模式。"),
    ("能耗查询", "查一下今天家里的能耗排行。"),
    ("吃药提醒", "提醒爷爷晚上九点吃降压药，如果十分钟没回应就再提醒一次。"),
    ("敏感动作", "帮我把门锁解锁。"),
]

MODEL_MODE_AUTO = "自动闭环（推荐）"
MODEL_MODE_RULE_ONLY = "规则仅调试（关闭模型）"
MODEL_MODE_FORCE_LOCAL = "调试：强制模型识别（仍走工具）"
LLM_DEMO_PROMPT = "老人那边视频总是一顿一顿的，先看看是不是网络问题。"


def _device_summary(state: dict) -> list[list[str]]:
    rows = []
    for did, info in state.get("devices", {}).items():
        status_icon = "🟢" if info.get("power") == "on" else "⚪"
        if info.get("type") == "lock":
            status_icon = "🔒" if info.get("locked") else "🔓"
        detail_parts: list[str] = []
        if "brightness" in info:
            detail_parts.append(f"亮度 {info['brightness']}%")
        if "temperature" in info:
            detail_parts.append(f"{info['temperature']}℃")
        if "mode" in info:
            detail_parts.append(f"模式 {info['mode']}")
        rows.append([
            info.get("room", "-"),
            info.get("name", did),
            status_icon,
            ", ".join(detail_parts) or "-",
        ])
    return rows


def _sensor_summary(state: dict) -> list[list[str]]:
    rows = []
    for room, s in state.get("sensors", {}).items():
        rows.append([
            room,
            f"{s.get('temperature')}℃",
            f"{s.get('humidity')}%",
            "有人" if s.get("motion") else f"{s.get('last_motion_min', 0)} 分钟无活动",
            f"{s.get('noise_db')} dB",
        ])
    return rows


def _energy_summary(state: dict) -> str:
    energy = state.get("energy", {})
    daily = energy.get("daily_kwh", 0)
    threshold = energy.get("threshold_kwh", 0)
    cost = round(daily * energy.get("price_per_kwh", 0), 2)
    badge = "⚠️ 已超阈值" if daily > threshold else "✅ 正常"
    return f"今日能耗 **{daily} kWh** ｜ 预计电费 **¥{cost}** ｜ 阈值 {threshold} kWh ｜ {badge}"


def _profile_summary(state: dict) -> str:
    profiles = state.get("family_profiles", {})
    lines = []
    for member, profile in profiles.items():
        parts = []
        if profile.get("personality"):
            parts.append("性格：" + "、".join(profile["personality"]))
        if profile.get("hobbies"):
            parts.append("爱好：" + "、".join(profile["hobbies"]))
        if profile.get("diet"):
            parts.append("饮食：" + "、".join(profile["diet"]))
        if profile.get("notes"):
            parts.append("备注：" + "、".join(profile["notes"]))
        if parts:
            lines.append(f"**{member}**｜" + "；".join(parts))
    return "\n\n".join(lines) if lines else "_还没有长期家庭画像。_"


def _format_metrics(metrics: dict) -> str:
    return (
        f"⏱ 总延迟 **{metrics.get('total_latency_ms')} ms** ｜ "
        f"NLU **{metrics.get('nlu_latency_ms')} ms**（模型 {metrics.get('model_latency_ms')} ms）｜ "
        f"工具 **{metrics.get('tool_latency_ms')} ms** ｜ "
        f"内存 ~ **{metrics.get('memory_mb')} MB**"
    )


def _format_plan(plan: list[dict]) -> str:
    if not plan:
        return "_本轮未触发任务规划。_"
    lines = ["| 步骤 | 工具 | 入参 | 依赖 |", "|---|---|---|---|"]
    for step in plan:
        deps = ",".join(step.get("depends_on", [])) or "-"
        args = json.dumps(step.get("args", {}), ensure_ascii=False)
        if len(args) > 80:
            args = args[:78] + "…"
        lines.append(f"| {step['step_id']} | `{step['tool']}` | {args} | {deps} |")
    return "\n".join(lines)


def _format_tool_log(tool_results: list[dict]) -> str:
    if not tool_results:
        return "_无工具调用。_"
    lines = []
    for r in tool_results:
        status = "✅" if r.get("status") == "success" else ("⚠️" if r.get("status") == "blocked" else "❌")
        lines.append(f"{status} `{r['tool']}` ({r.get('duration_ms', 0)} ms) — {r.get('message', '')}")
    return "\n\n".join(lines)


def _format_intent(intent: dict) -> str:
    src = intent.get("source", "rule")
    badge = "📐 规则" if src == "rule" else "🧠 本地模型"
    return (
        f"**意图**：`{intent.get('name')}` ｜ 置信度 {intent.get('confidence', 0):.2f} ｜ {badge}\n\n"
        f"**理由**：{intent.get('reasoning', '')}"
    )


def _config_from_model_mode(model_mode: str) -> dict:
    force_local = model_mode == MODEL_MODE_FORCE_LOCAL
    rule_only = model_mode == MODEL_MODE_RULE_ONLY
    return {
        "mode": "llm" if force_local else "hybrid",
        "force_local_llm": force_local,
        "enable_local_llm": not rule_only,
    }


def _format_model_status(result: dict | None) -> str:
    if not result:
        return "_等待请求后显示模型状态。_"
    metrics = result.get("metrics", {})
    attempted = bool(metrics.get("model_attempted") or metrics.get("answer_model_attempted"))
    available = bool(metrics.get("model_available") or metrics.get("answer_model_available"))
    raw = str(metrics.get("model_raw_output") or "").strip()
    cache_hit = bool(metrics.get("model_cache_hit"))
    answer_attempted = bool(metrics.get("answer_model_attempted"))
    answer_raw = str(metrics.get("answer_model_raw_output") or "").strip()
    if len(raw) > 240:
        raw = raw[:238] + "…"
    if len(answer_raw) > 240:
        answer_raw = answer_raw[:238] + "…"
    if not attempted:
        return "📐 本轮未调用本地模型：规则路径已命中。"
    lines = []
    if available:
        if cache_hit:
            lines.append(f"🧠 本轮命中本地 Qwen 意图缓存，耗时 **{metrics.get('model_latency_ms')} ms**。")
        else:
            lines.append(f"🧠 本轮已调用本地 Qwen 模型，总耗时 **{metrics.get('model_latency_ms')} ms**。")
        if result.get("tool_results"):
            lines.append("说明：本轮是“本地模型补识别意图 + 工具执行”，最终回复由工具结果汇总生成。")
        elif answer_attempted:
            lines.append("说明：没有可执行工具或可信知识命中，本轮才进入本地模型直接回答兜底。")
        if raw:
            lines.append(f"意图识别输出：`{raw}`")
        if answer_attempted:
            lines.append(
                f"直接回答输出（{metrics.get('answer_model_latency_ms')} ms）：`{answer_raw or '空'}`"
            )
        return "\n\n".join(lines)
    error = metrics.get("model_error") or metrics.get("answer_model_error") or "未知错误"
    return f"⚠️ 本轮尝试调用本地模型但不可用：`{error}`"


def chat_handler(user_input: str, history: list, state: dict | None, model_mode: str):
    history = history or []
    state = state or {}
    user_input = (user_input or "").strip()
    if not user_input:
        return history, state, "_请输入指令。_", "_等待请求后显示模型状态。_", _profile_summary(state), "_无规划。_", "_无工具日志。_", [], [], "", "_无指标。_"

    result = run(user_input, state=state, config=_config_from_model_mode(model_mode))
    new_state = result["state"]

    history = history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": result["reply"]},
    ]
    return (
        history,
        new_state,
        _format_intent(result["intent"]),
        _format_model_status(result),
        _profile_summary(new_state),
        _format_plan(result["plan"]),
        _format_tool_log(result["tool_results"]),
        _device_summary(new_state),
        _sensor_summary(new_state),
        _energy_summary(new_state),
        _format_metrics(result["metrics"]),
    )


def reset_handler():
    state = _load_persistent_profiles({})
    return [], state, "_已重置会话。_", "_等待请求后显示模型状态。_", _profile_summary(state), "_无规划。_", "_无工具日志。_", [], [], "", "_无指标。_"


def refresh_profiles_handler(state: dict | None):
    state = _load_persistent_profiles(state or {})
    return state, _profile_summary(state)


def _load_persistent_profiles(state: dict) -> dict:
    memory = FamilyProfileMemory(DEFAULT_CONFIG.get("sqlite_path"))
    state = dict(state or {})
    state["family_profiles"] = memory.load()
    return state


def _preload_local_model() -> None:
    try:
        get_cached_local_llm_client(DEFAULT_CONFIG).status(load=True)
    except Exception:
        pass


def build_app() -> gr.Blocks:
    with gr.Blocks(title="兴享智家·慧家中枢", theme=gr.themes.Soft()) as app:
        gr.Markdown(
            """
            # 🏠 兴享智家·慧家中枢
            端侧 Agent · 规则路由优先 · 本地小模型兜底 · SQLite 知识库 · 主动感知
            """
        )

        initial_state = _load_persistent_profiles({})
        state = gr.State(initial_state)

        with gr.Row():
            with gr.Column(scale=5):
                chatbot = gr.Chatbot(label="对话窗口", type="messages", height=420)
                with gr.Row():
                    user_box = gr.Textbox(
                        placeholder="例如：帮老人那屋弄得舒服一点 / 一键巡检 / 切睡前模式",
                        label="用户输入",
                        scale=8,
                    )
                    send_btn = gr.Button("发送", variant="primary", scale=1)
                    reset_btn = gr.Button("重置", scale=1)

                gr.Markdown("### 🎯 快捷场景")
                with gr.Row():
                    shortcut_buttons = [gr.Button(label) for label, _ in SHORTCUTS]
                llm_demo_btn = gr.Button("强制模型识别调试", variant="secondary")

            with gr.Column(scale=4):
                model_mode = gr.Radio(
                    choices=[MODEL_MODE_AUTO, MODEL_MODE_RULE_ONLY, MODEL_MODE_FORCE_LOCAL],
                    value=MODEL_MODE_AUTO,
                    label="运行策略",
                )
                intent_md = gr.Markdown("_意图识别将在这里显示。_", label="意图")
                model_md = gr.Markdown("_等待请求后显示模型状态。_", label="本地模型状态")
                with gr.Accordion("🧠 长期家庭画像", open=True):
                    profile_md = gr.Markdown(_profile_summary(initial_state))
                    refresh_profile_btn = gr.Button("刷新长期记忆", variant="secondary")
                with gr.Accordion("📋 任务规划 (DAG)", open=True):
                    plan_md = gr.Markdown("_无规划。_")
                with gr.Accordion("🔧 工具调用日志", open=True):
                    tool_md = gr.Markdown("_无工具日志。_")
                with gr.Accordion("💡 设备状态面板", open=True):
                    devices_table = gr.Dataframe(
                        headers=["房间", "设备", "状态", "详情"],
                        datatype=["str", "str", "str", "str"],
                        interactive=False,
                        label="设备",
                    )
                with gr.Accordion("🌡 传感器面板", open=False):
                    sensors_table = gr.Dataframe(
                        headers=["房间", "温度", "湿度", "活动", "噪声"],
                        datatype=["str", "str", "str", "str", "str"],
                        interactive=False,
                        label="传感器",
                    )
                energy_md = gr.Markdown("", label="能耗")

        metrics_md = gr.Markdown("_性能指标将在这里显示。_")

        outputs = [
            chatbot,
            state,
            intent_md,
            model_md,
            profile_md,
            plan_md,
            tool_md,
            devices_table,
            sensors_table,
            energy_md,
            metrics_md,
        ]

        send_btn.click(chat_handler, [user_box, chatbot, state, model_mode], outputs).then(
            lambda: "", None, user_box
        )
        user_box.submit(chat_handler, [user_box, chatbot, state, model_mode], outputs).then(
            lambda: "", None, user_box
        )
        reset_btn.click(reset_handler, None, outputs)
        refresh_profile_btn.click(refresh_profiles_handler, state, [state, profile_md])

        for btn, (_, prompt) in zip(shortcut_buttons, SHORTCUTS):
            btn.click(lambda p=prompt: p, None, user_box).then(
                chat_handler, [user_box, chatbot, state, model_mode], outputs
            ).then(lambda: "", None, user_box)
        llm_demo_btn.click(
            lambda: (LLM_DEMO_PROMPT, MODEL_MODE_FORCE_LOCAL),
            None,
            [user_box, model_mode],
        ).then(chat_handler, [user_box, chatbot, state, model_mode], outputs).then(
            lambda: "", None, user_box
        )

    return app


if __name__ == "__main__":
    threading.Thread(target=_preload_local_model, daemon=True).start()
    build_app().launch(server_name="127.0.0.1", server_port=7860, share=False, inbrowser=True)
