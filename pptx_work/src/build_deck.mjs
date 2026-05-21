import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  layers,
  panel,
  text,
  shape,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  fr,
  auto,
} from "@oai/artifact-tool";

const SLIDE = { width: 1920, height: 1080 };
const OUT_DIR = path.resolve("output");
const PREVIEW_DIR = path.resolve("scratch", "previews");
const PPTX_NAME = process.env.PPTX_NAME || "output.pptx";

const C = {
  bg: "#08111F",
  bg2: "#0E1B2D",
  ink: "#142033",
  paper: "#F7FAFC",
  paper2: "#EDF4F7",
  white: "#FFFFFF",
  text: "#EAF3F2",
  muted: "#9FB3BE",
  muted2: "#5A6B76",
  teal: "#2DD4BF",
  green: "#33C979",
  amber: "#F3B454",
  blue: "#5CB6F2",
  red: "#F87171",
  line: "#264257",
  deep: "#122034",
};

const typography = {
  title: { fontSize: 58, bold: true, color: C.text },
  titleDark: { fontSize: 58, bold: true, color: C.ink },
  subtitle: { fontSize: 28, color: C.muted },
  body: { fontSize: 25, color: C.text },
  bodyDark: { fontSize: 25, color: C.ink },
  small: { fontSize: 18, color: C.muted },
  smallDark: { fontSize: 18, color: C.muted2 },
  label: { fontSize: 19, bold: true, color: C.teal },
};

const presentation = Presentation.create({ slideSize: SLIDE });

function addSlide(name, background, content) {
  const slide = presentation.slides.add();
  slide.compose(
    layers({ name: `${name}-root`, width: fill, height: fill }, [
      shape({ name: `${name}-bg`, width: fill, height: fill, fill: background }),
      content,
    ]),
    { frame: { left: 0, top: 0, width: SLIDE.width, height: SLIDE.height }, baseUnit: 8 },
  );
  return slide;
}

function footer(slideNo, dark = false) {
  return row(
    { name: `footer-${slideNo}`, width: fill, height: hug, justify: "between", align: "center" },
    [
      text("兴享智家 · 慧家中枢复赛答辩", {
        width: hug,
        height: hug,
        style: dark ? typography.smallDark : typography.small,
      }),
      text(`${String(slideNo).padStart(2, "0")}/11`, {
        width: fixed(80),
        height: hug,
        style: { fontSize: 18, bold: true, color: dark ? C.muted2 : C.muted },
      }),
    ],
  );
}

function titleStack(title, subtitle, dark = false) {
  return column({ name: "title-stack", width: fill, height: hug, gap: 18 }, [
    text(title, {
      name: "slide-title",
      width: wrap(1420),
      height: hug,
      style: dark ? typography.titleDark : typography.title,
    }),
    subtitle
      ? text(subtitle, {
          name: "slide-subtitle",
          width: wrap(1420),
          height: hug,
          style: dark ? { ...typography.subtitle, color: C.muted2 } : typography.subtitle,
        })
      : rule({ name: "title-rule", width: fixed(180), stroke: dark ? C.ink : C.teal, weight: 4 }),
  ].filter(Boolean));
}

function pill(label, color = C.teal, dark = false) {
  return panel(
    {
      name: `pill-${label}`,
      width: hug,
      height: hug,
      fill: dark ? "#E7F8F4" : C.deep,
      padding: { x: 20, y: 10 },
      borderRadius: "rounded-full",
    },
    text(label, {
      width: hug,
      height: hug,
      style: { fontSize: 18, bold: true, color },
    }),
  );
}

function bullet(copy, color = C.teal, dark = false) {
  return row({ name: `bullet-${copy.slice(0, 8)}`, width: fill, height: hug, gap: 18, align: "start" }, [
    shape({ name: "bullet-dot", geometry: "ellipse", width: fixed(13), height: fixed(13), fill: color }),
    text(copy, {
      width: fill,
      height: hug,
      style: dark ? typography.bodyDark : typography.body,
    }),
  ]);
}

function softPanel(name, child, fillColor = "#122238", padding = { x: 30, y: 26 }) {
  return panel(
    {
      name,
      width: fill,
      height: fill,
      fill: fillColor,
      padding,
      borderRadius: 12,
    },
    child,
  );
}

function metric(label, value, note, color = C.teal) {
  return column({ name: `metric-${label}`, width: fill, height: hug, gap: 8 }, [
    text(value, { width: fill, height: hug, style: { fontSize: 48, bold: true, color } }),
    text(label, { width: fill, height: hug, style: { fontSize: 22, bold: true, color: C.text } }),
    text(note, { width: fill, height: hug, style: { fontSize: 17, color: C.muted } }),
  ]);
}

function stage(label, note, color = C.teal) {
  return panel(
    {
      name: `stage-${label}`,
      width: fill,
      height: fixed(148),
      fill: "#122238",
      padding: { x: 20, y: 18 },
      borderRadius: 12,
    },
    column({ width: fill, height: fill, gap: 10, justify: "center" }, [
      text(label, { width: fill, height: hug, style: { fontSize: 25, bold: true, color } }),
      text(note, { width: fill, height: hug, style: { fontSize: 17, color: C.muted } }),
    ]),
  );
}

function tableCell(copy, header = false, color = C.text) {
  return text(copy, {
    width: fill,
    height: hug,
    style: { fontSize: header ? 21 : 20, bold: header, color },
  });
}

// 1. Cover
addSlide(
  "cover",
  C.bg,
  column({ name: "cover-flow", width: fill, height: fill, padding: { x: 96, y: 74 }, justify: "between" }, [
    row({ width: fill, height: hug, justify: "between", align: "center" }, [
      text("复赛作品展示", { width: hug, height: hug, style: { fontSize: 22, bold: true, color: C.teal } }),
      text("西安电子科技大学广州研究院", { width: hug, height: hug, style: { fontSize: 20, color: C.muted } }),
    ]),
    column({ width: fill, height: hug, gap: 28 }, [
      text("兴享智家", {
        name: "cover-title",
        width: wrap(980),
        height: hug,
        style: { fontSize: 118, bold: true, color: C.white },
      }),
      text("慧家中枢", {
        width: wrap(760),
        height: hug,
        style: { fontSize: 72, bold: true, color: C.teal },
      }),
      rule({ width: fixed(360), stroke: C.amber, weight: 5 }),
      text("面向三代同堂家庭的本地智能体：把老人关怀、睡前联动、网络 QoS 与安全巡检做成可解释、可演示、可端侧运行的闭环。", {
        width: wrap(1220),
        height: hug,
        style: { fontSize: 31, color: C.muted },
      }),
    ]),
    row({ width: fill, height: hug, justify: "between", align: "end" }, [
      row({ width: hug, height: hug, gap: 14 }, [
        pill("端侧", C.teal),
        pill("本地 LLM", C.blue),
        pill("任务规划", C.green),
        pill("长期记忆", C.amber),
      ]),
      text("答辩重点：作品定位、个人承担、现场 demo", {
        width: hug,
        height: hug,
        style: { fontSize: 20, color: C.muted },
      }),
    ]),
  ]),
);

// 2. Defense story
addSlide(
  "revision",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 92, y: 72 }, justify: "between", gap: 34 }, [
    titleStack("答辩主线：证明它是本地家庭中枢", "展示重点不是泛聊天，而是四条家庭任务链路真实闭环、可追踪、可解释。", true),
    row({ width: fill, height: fill, gap: 42, align: "stretch" }, [
      column({ width: fill, height: fill, gap: 20, justify: "center" }, [
        text("作品边界", { width: fill, height: hug, style: { fontSize: 32, bold: true, color: C.ink } }),
        bullet("不做“什么都聊一点”的家庭聊天机器人。", C.teal, true),
        bullet("聚焦老人关怀、睡前联动、网络 QoS、主动巡检。", C.teal, true),
        bullet("知识问答、儿童学习、能耗分析作为辅助能力。", C.teal, true),
      ]),
      shape({ width: fixed(5), height: fill, fill: C.teal }),
      column({ width: fill, height: fill, gap: 20, justify: "center" }, [
        text("能力证明", { width: fill, height: hug, style: { fontSize: 32, bold: true, color: C.ink } }),
        bullet("每轮请求可追踪 intent source、plan、tool_results 和 metrics。", C.green, true),
        bullet("规则优先保证主线稳定，本地 Qwen 负责模糊表达和兜底回答。", C.green, true),
        bullet("SQLite 长期画像 + 会话历史，让家庭成员偏好可持续使用。", C.green, true),
      ]),
    ]),
    footer(2, true),
  ]),
);

// 3. Product scope
addSlide(
  "scope",
  C.bg2,
  column({ width: fill, height: fill, padding: { x: 88, y: 70 }, justify: "between", gap: 28 }, [
    titleStack("产品定位：三代同堂家庭的本地家庭中枢", "主舞台只讲四件事，儿童学习与能耗作为加分能力；知识问答降级为辅助解释。"),
    grid({ width: fill, height: fill, columns: [fr(1), fr(1)], rows: [fr(1), fr(1), fr(0.72)], columnGap: 28, rowGap: 24 }, [
      softPanel("care", column({ width: fill, height: fill, gap: 12 }, [
        text("老人关怀", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        text("吃药提醒、未响应复提醒、老人房状态巡检、偏好记忆。", { width: fill, height: hug, style: typography.body }),
      ])),
      softPanel("sleep", column({ width: fill, height: fill, gap: 12 }, [
        text("睡前场景联动", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.amber } }),
        text("灯光、电视、空调、门锁、老人提醒一次性编排。", { width: fill, height: hug, style: typography.body }),
      ])),
      softPanel("network", column({ width: fill, height: fill, gap: 12 }, [
        text("网络诊断与 QoS", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.blue } }),
        text("定位老人房视频卡顿，识别带宽占用，并多轮确认开启优先级。", { width: fill, height: hug, style: typography.body }),
      ])),
      softPanel("alert", column({ width: fill, height: fill, gap: 12 }, [
        text("主动巡检与安全确认", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.green } }),
        text("全屋传感器读取，敏感动作二次确认，工具日志可回溯。", { width: fill, height: hug, style: typography.body }),
      ])),
      text("加分能力：儿童学习 / 睡眠模式、能耗分析、长期家庭画像、本地知识解释", {
        columnSpan: 2,
        width: fill,
        height: hug,
        style: { fontSize: 28, bold: true, color: C.text },
      }),
    ]),
    footer(3),
  ]),
);

// 4. Architecture
addSlide(
  "architecture",
  C.bg,
  column({ width: fill, height: fill, padding: { x: 78, y: 66 }, justify: "between", gap: 32 }, [
    titleStack("总体架构：从自然语言到可解释工具闭环", "每轮输出不仅有回复，还包含 intent、DAG plan、tool_results、state、metrics 和 safety。"),
    grid({ width: fill, height: hug, columns: [fr(1), auto, fr(1), auto, fr(1), auto, fr(1), auto, fr(1), auto, fr(1)], columnGap: 14, alignItems: "center" }, [
      stage("用户输入", "家庭自然语言"),
      text("→", { width: hug, height: hug, style: { fontSize: 42, bold: true, color: C.teal } }),
      stage("LocalRouter", "规则优先 + LLM 兜底", C.blue),
      text("→", { width: hug, height: hug, style: { fontSize: 42, bold: true, color: C.teal } }),
      stage("TaskPlanner", "意图转 DAG", C.amber),
      text("→", { width: hug, height: hug, style: { fontSize: 42, bold: true, color: C.teal } }),
      stage("Executor", "拓扑执行 + 安全门", C.green),
      text("→", { width: hug, height: hug, style: { fontSize: 42, bold: true, color: C.teal } }),
      stage("Tools / Memory", "设备、网络、SQLite", C.blue),
      text("→", { width: hug, height: hug, style: { fontSize: 42, bold: true, color: C.teal } }),
      stage("Reply", "解释结果与指标", C.teal),
    ]),
    row({ width: fill, height: fill, gap: 30 }, [
      softPanel("arch-code", column({ width: fill, height: fill, gap: 16 }, [
        text("关键文件", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.teal } }),
        text("pipeline.py 串联 Agent 主流程\nrouter.py 完成意图识别\nplanner.py 生成 DAG 计划\nexecutor.py 执行工具与安全确认\nhome_tools.py 注册家庭工具\nlocal_llm.py 加载本地 Qwen\nfamily_profile.py 持久化画像", {
          width: fill,
          height: hug,
          style: { fontSize: 23, color: C.text },
        }),
      ])),
      softPanel("arch-return", column({ width: fill, height: fill, gap: 16 }, [
        text("答辩可追问性", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.amber } }),
        text("评委问“为什么这么做”：看 intent source。\n评委问“做了什么”：看 plan 和 tool_results。\n评委问“模型有没有参与”：看 model metrics。\n评委问“是否端侧”：看本地 GGUF + SQLite + 无外部 API。", {
          width: fill,
          height: hug,
          style: { fontSize: 23, color: C.text },
        }),
      ])),
    ]),
    footer(4),
  ]),
);

// 5. Local LLM
addSlide(
  "llm",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 88, y: 68 }, justify: "between", gap: 30 }, [
    titleStack("本地模型接入：让 local_llm 成为真实能力", "规则无法覆盖或知识库无可信答案时，才进入本地 Qwen 兜底；前端和返回指标会显示真实调用情况。", true),
    row({ width: fill, height: fill, gap: 36, align: "stretch" }, [
      column({ width: fill, height: fill, gap: 22, justify: "center" }, [
        text("路由策略", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.ink } }),
        bullet("主线场景：规则路径，保证稳定和低延迟。", C.teal, true),
        bullet("模糊表达：规则 unknown 后调用 classify_intent。", C.blue, true),
        bullet("普通问题：unknown 或知识库无命中时调用 generate_reply。", C.green, true),
        bullet("安全与画像写入：受保护规则，不被强制模型覆盖。", C.amber, true),
      ]),
      softPanel("llm-metrics", column({ width: fill, height: fill, gap: 24, justify: "center" }, [
        text("可证明的模型指标", { width: fill, height: hug, style: { fontSize: 32, bold: true, color: C.teal } }),
        metric("模型是否尝试调用", "model_attempted", "分类阶段可追踪", C.blue),
        metric("模型是否成功可用", "model_available", "加载失败会显式降级", C.green),
        metric("直接回答原始输出", "answer_model_raw_output", "证明不是纯 if-else", C.amber),
      ])),
    ]),
    footer(5, true),
  ]),
);

// 6. Planning and safety
addSlide(
  "planning",
  C.bg2,
  column({ width: fill, height: fill, padding: { x: 82, y: 66 }, justify: "between", gap: 28 }, [
    titleStack("任务规划：理解意图 → 生成 DAG → 调工具 → 更新状态", "系统不直接“凭文本回复”，而是把任务拆成可执行步骤，再由工具结果生成自然语言。"),
    row({ width: fill, height: fill, gap: 34 }, [
      softPanel("dag", column({ width: fill, height: fill, gap: 18 }, [
        text("睡前模式示例 DAG", { width: fill, height: hug, style: { fontSize: 32, bold: true, color: C.teal } }),
        text("s1  home_profile.query\ns2  scene.apply\ns3  device.query\ns4  reminder.query", {
          width: fill,
          height: hug,
          style: { fontSize: 30, color: C.text },
        }),
        rule({ width: fill, stroke: C.line, weight: 2 }),
        text("输出：灯光/电视/空调联动，门锁状态检查，老人提醒同步查询。", {
          width: fill,
          height: hug,
          style: { fontSize: 22, color: C.muted },
        }),
      ])),
      softPanel("safety", column({ width: fill, height: fill, gap: 18 }, [
        text("敏感动作安全门", { width: fill, height: hug, style: { fontSize: 32, bold: true, color: C.amber } }),
        text("解锁门锁 / 关闭摄像头 / 取消告警\n不会直接执行，先写入 pending_confirmations。", {
          width: fill,
          height: hug,
          style: { fontSize: 26, color: C.text },
        }),
        rule({ width: fill, stroke: C.line, weight: 2 }),
        text("用户说“确认执行”后，planner 读取 pending action 并补 confirmed=True，再继续执行。", {
          width: fill,
          height: hug,
          style: { fontSize: 22, color: C.muted },
        }),
      ])),
    ]),
    footer(6),
  ]),
);

// 7. Memory and knowledge
addSlide(
  "memory",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 86, y: 68 }, justify: "between", gap: 30 }, [
    titleStack("记忆能力：短期承接上下文，长期沉淀家庭画像", "这次新增的重点不是“更会闲聊”，而是让系统记住每个家庭成员真实偏好，并在任务中使用。", true),
    grid({ width: fill, height: fill, columns: [fr(1), fr(1), fr(1)], columnGap: 26 }, [
      softPanel("short-memory", column({ width: fill, height: fill, gap: 16 }, [
        text("短期会话记忆", { width: fill, height: hug, style: { fontSize: 31, bold: true, color: C.ink } }),
        text("state.history\n最近 12 条对话\nLLM 直接回答读取最近 6 条", { width: fill, height: hug, style: { fontSize: 25, color: C.ink } }),
        text("例：问“什么步骤”时承接上一轮可乐鸡翅。", { width: fill, height: hug, style: { fontSize: 20, color: C.muted2 } }),
      ]), "#EAF6F4"),
      softPanel("profile-memory", column({ width: fill, height: fill, gap: 16 }, [
        text("长期家庭画像", { width: fill, height: hug, style: { fontSize: 31, bold: true, color: C.ink } }),
        text("SQLite family_profiles\n性格 / 爱好 / 饮食 / 备注\n重启后仍可读取", { width: fill, height: hug, style: { fontSize: 25, color: C.ink } }),
        text("例：记住爷爷不吃辣，午餐推荐避开辣菜。", { width: fill, height: hug, style: { fontSize: 20, color: C.muted2 } }),
      ]), "#EEF4FF"),
      softPanel("knowledge", column({ width: fill, height: fill, gap: 16 }, [
        text("知识辅助边界", { width: fill, height: hug, style: { fontSize: 31, bold: true, color: C.ink } }),
        text("SQLite 知识库\n最低命中阈值\n无来源不编造", { width: fill, height: hug, style: { fontSize: 25, color: C.ink } }),
        text("有来源展示标题和 score；无命中转 LLM 或保守拒答。", { width: fill, height: hug, style: { fontSize: 20, color: C.muted2 } }),
      ]), "#FFF4DF"),
    ]),
    footer(7, true),
  ]),
);

// 8. Function implementation matrix
addSlide(
  "functions",
  C.bg,
  column({ width: fill, height: fill, padding: { x: 80, y: 62 }, justify: "between", gap: 24 }, [
    titleStack("功能清单与实现方式", "每个现场演示动作都能对应到意图、规划与工具调用，而不是停留在界面效果。"),
    softPanel(
      "function-table",
      grid({ width: fill, height: fill, columns: [fr(0.9), fr(1.05), fr(1.45), fr(1.65)], rows: [auto, auto, auto, auto, auto, auto, auto], columnGap: 24, rowGap: 17 }, [
        tableCell("能力", true, C.teal),
        tableCell("意图", true, C.teal),
        tableCell("核心工具", true, C.teal),
        tableCell("答辩价值", true, C.teal),
        tableCell("睡前联动"),
        tableCell("scene_mode_apply"),
        tableCell("scene.apply / device.query"),
        tableCell("场景化智能体与多设备编排"),
        tableCell("老人网络 QoS"),
        tableCell("network_diagnose / apply_qos"),
        tableCell("network.diagnose / network.apply_qos"),
        tableCell("多轮状态继承与策略执行"),
        tableCell("吃药提醒"),
        tableCell("reminder_create / query"),
        tableCell("reminder.create / reminder.query"),
        tableCell("老人关怀与未响应复提醒"),
        tableCell("主动巡检"),
        tableCell("proactive_alert"),
        tableCell("sensor.query / sensor.check_alert"),
        tableCell("传感器规则与安全确认"),
        tableCell("长期画像"),
        tableCell("profile_memory_update / query"),
        tableCell("profile.remember / profile.query"),
        tableCell("家庭成员个性化和持久记忆"),
        tableCell("知识解释"),
        tableCell("knowledge_query"),
        tableCell("knowledge.search + LLM fallback"),
        tableCell("本地来源约束，降低误答风险"),
      ]),
      "#102137",
      { x: 34, y: 30 },
    ),
    footer(8),
  ]),
);

// 9. Demo script
addSlide(
  "demo",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 90, y: 66 }, justify: "between", gap: 26 }, [
    titleStack("现场 Demo：3 分钟讲清 4 条黄金链路", "建议先讲定位，再连续触发闭环，让评委看到 intent、plan、tools、metrics 同步变化。", true),
    row({ width: fill, height: fill, gap: 48 }, [
      column({ width: fill, height: fill, gap: 18, justify: "center" }, [
        bullet("1. 睡前模式：爸妈准备睡了，检查门锁和老人提醒。", C.teal, true),
        bullet("2. 网络卡顿：爷爷房间视频有点卡，诊断后“先保证爷爷那边”。", C.blue, true),
        bullet("3. 老人提醒：提醒爷爷 21:00 吃药，未响应 10 分钟复提醒。", C.green, true),
        bullet("4. 长期画像：记住爷爷不吃辣，中午推荐时自动避开。", C.amber, true),
        bullet("5. 主动巡检：检查全屋，发现老人房低温或长时间无活动。", C.red, true),
      ]),
      softPanel("demo-panel", column({ width: fill, height: fill, gap: 20, justify: "center" }, [
        text("展示界面要让评委看到", { width: fill, height: hug, style: { fontSize: 31, bold: true, color: C.teal } }),
        text("当前意图来源\n任务规划 DAG\n工具执行轨迹\n本地模型状态\n长期家庭画像\n端侧性能指标", {
          width: fill,
          height: hug,
          style: { fontSize: 31, color: C.text },
        }),
      ])),
    ]),
    footer(9, true),
  ]),
);

// 10. Personal contribution
addSlide(
  "contribution",
  C.bg2,
  column({ width: fill, height: fill, padding: { x: 88, y: 70 }, justify: "between", gap: 30 }, [
    titleStack("我承担的部分：算法工程与可演示闭环", "团队赛答辩时建议把个人贡献讲成“问题发现 → 工程实现 → 验证交付”。"),
    row({ width: fill, height: fill, gap: 34, align: "stretch" }, [
      column({ width: fill, height: fill, gap: 22, justify: "center" }, [
        text("主要负责", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        bullet("Agent 主链路：router、planner、executor、pipeline。"),
        bullet("本地 LLM：Qwen GGUF 加载、分类、直接回答、调用指标。", C.blue),
        bullet("记忆与知识：长期家庭画像、短期历史、知识无命中回退。", C.green),
        bullet("演示工程：Gradio 前端状态面板、模型策略切换、测试脚本。", C.amber),
      ]),
      softPanel("contrib-output", column({ width: fill, height: fill, gap: 22, justify: "center" }, [
        text("可交付结果", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.amber } }),
        text("技术说明文档\n答辩 PPT\n自动化场景测试\n本地模型演示脚本\n长期记忆演示脚本\n现场 demo 脚本", {
          width: fill,
          height: hug,
          style: { fontSize: 29, color: C.text },
        }),
        text("如团队分工有调整，这页可直接替换为真实姓名与模块边界。", {
          width: fill,
          height: hug,
          style: { fontSize: 19, color: C.muted },
        }),
      ])),
    ]),
    footer(10),
  ]),
);

// 11. Validation and defense
addSlide(
  "validation",
  C.bg,
  column({ width: fill, height: fill, padding: { x: 86, y: 70 }, justify: "between", gap: 30 }, [
    titleStack("验收口径：稳定演示，也能经得起追问", "评审不只看界面，更会问“模型是否真实、工具是否执行、状态是否保持、端侧是否成立”。"),
    row({ width: fill, height: fill, gap: 32, align: "stretch" }, [
      softPanel("acceptance", column({ width: fill, height: fill, gap: 20 }, [
        text("当前硬门槛", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        bullet("主线 4 场景可连续演示。"),
        bullet("敏感动作二次确认不漏拦截。", C.amber),
        bullet("本地模型可通过 metrics 与脚本证明。", C.blue),
        bullet("SQLite 本地存储，断网核心流程可运行。", C.green),
        bullet("测试脚本覆盖长期画像、QoS、巡检、温度查询等场景。", C.teal),
      ])),
      softPanel("next", column({ width: fill, height: fill, gap: 20 }, [
        text("下一步增强", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.amber } }),
        bullet("接入真实设备适配层：Matter / Home Assistant / MQTT。"),
        bullet("用本地 LLM 辅助画像结构化抽取，并保留规则校验。", C.blue),
        bullet("增加多用户会话隔离和性能压测报告。", C.green),
        bullet("录制一版 3 分钟稳定讲解视频，现场作为备份。", C.teal),
      ])),
    ]),
    row({ width: fill, height: hug, justify: "between", align: "center" }, [
      text("一句话收束：兴享智家不是泛聊天机器人，而是面向家庭任务的本地智能中枢。", {
        width: wrap(1320),
        height: hug,
        style: { fontSize: 30, bold: true, color: C.text },
      }),
      text("11/11", { width: fixed(80), height: hug, style: { fontSize: 18, bold: true, color: C.muted } }),
    ]),
  ]),
);

await mkdir(OUT_DIR, { recursive: true });
await mkdir(PREVIEW_DIR, { recursive: true });

const pptxBlob = await PresentationFile.exportPptx(presentation);
await pptxBlob.save(path.join(OUT_DIR, PPTX_NAME));

for (let i = 0; i < presentation.slides.count; i += 1) {
  const slide = presentation.slides.getItem(i);
  const pngBlob = await slide.export({ format: "png" });
  const buffer = Buffer.from(await pngBlob.arrayBuffer());
  await writeFile(path.join(PREVIEW_DIR, `slide-${String(i + 1).padStart(2, "0")}.png`), buffer);
}

console.log(JSON.stringify({ slides: presentation.slides.count, pptx: path.join(OUT_DIR, PPTX_NAME), previews: PREVIEW_DIR }));
