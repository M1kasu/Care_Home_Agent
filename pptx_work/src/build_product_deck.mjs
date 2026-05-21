import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  image,
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
const TOTAL_SLIDES = 20;
const OUT_DIR = path.resolve("output");
const PREVIEW_DIR = path.resolve("scratch", "product_previews");
const FRAMEWORK_IMAGE = "assets/project_framework.png";
const PPTX_NAME = process.env.PPTX_NAME || "兴享智家_慧家中枢_复赛产品介绍_评分维度强化版.pptx";

const C = {
  ink: "#17212D",
  ink2: "#243241",
  cloud: "#F6F8F4",
  paper: "#FFFDF7",
  mist: "#EAF3EF",
  line: "#D8E3DE",
  teal: "#0E8F86",
  mint: "#66D0B2",
  blue: "#3678D5",
  amber: "#E8A038",
  coral: "#E96D5B",
  green: "#37A56F",
  violet: "#7A6CE0",
  white: "#FFFFFF",
  quiet: "#6B7A86",
  quiet2: "#93A1A8",
  darkBg: "#0F1C28",
};

const type = {
  hero: { fontSize: 96, bold: true, color: C.white },
  h1: { fontSize: 56, bold: true, color: C.ink },
  h1Light: { fontSize: 56, bold: true, color: C.white },
  h2: { fontSize: 34, bold: true, color: C.ink },
  h2Light: { fontSize: 34, bold: true, color: C.white },
  body: { fontSize: 25, color: C.ink2 },
  bodyLight: { fontSize: 25, color: "#EAF2F0" },
  small: { fontSize: 18, color: C.quiet },
  smallLight: { fontSize: 18, color: "#A8B8BF" },
  label: { fontSize: 18, bold: true, color: C.teal },
};

const presentation = Presentation.create({ slideSize: SLIDE });

function addSlide(name, bg, child) {
  const slide = presentation.slides.add();
  const content =
    name === "project-framework"
      ? image({
          name: "project-framework-image",
          path: FRAMEWORK_IMAGE,
          width: fill,
          height: fill,
          fit: "contain",
          alt: "Overall project framework diagram",
        })
      : child;
  slide.compose(
    layers({ name: `${name}-root`, width: fill, height: fill }, [
      shape({ name: `${name}-bg`, width: fill, height: fill, fill: bg }),
      content,
    ]),
    { frame: { left: 0, top: 0, width: SLIDE.width, height: SLIDE.height }, baseUnit: 8 },
  );
}

function footer(page, light = false) {
  return row({ name: `footer-${page}`, width: fill, height: hug, justify: "between", align: "center" }, [
    text("兴享智家 · 慧家中枢｜复赛产品介绍", {
      width: hug,
      height: hug,
      style: light ? type.smallLight : type.small,
    }),
    text(String(page).padStart(2, "0") + `/${TOTAL_SLIDES}`, {
      width: fixed(90),
      height: hug,
      style: { fontSize: 18, bold: true, color: light ? "#A8B8BF" : C.quiet },
    }),
  ]);
}

function title(titleText, subText, light = false) {
  return column({ name: "title-block", width: fill, height: hug, gap: 18 }, [
    text(titleText, {
      name: "slide-title",
      width: wrap(1400),
      height: hug,
      style: light ? type.h1Light : type.h1,
    }),
    text(subText, {
      name: "slide-subtitle",
      width: wrap(1320),
      height: hug,
      style: light ? { fontSize: 26, color: "#B9C9C8" } : { fontSize: 26, color: C.quiet },
    }),
  ]);
}

function chip(label, color = C.teal, light = false) {
  return panel(
    {
      name: `chip-${label}`,
      width: hug,
      height: hug,
      padding: { x: 18, y: 8 },
      fill: light ? "#1B3140" : "#E7F4F1",
      borderRadius: "rounded-full",
    },
    text(label, { width: hug, height: hug, style: { fontSize: 18, bold: true, color } }),
  );
}

function bullet(textValue, color = C.teal, light = false) {
  return row({ name: `bullet-${textValue.slice(0, 8)}`, width: fill, height: hug, gap: 16, align: "start" }, [
    shape({ name: "dot", geometry: "ellipse", width: fixed(12), height: fixed(12), fill: color }),
    text(textValue, {
      width: fill,
      height: hug,
      style: light ? type.bodyLight : type.body,
    }),
  ]);
}

function plainPanel(name, child, fillColor = C.white, padding = { x: 28, y: 24 }) {
  return panel(
    {
      name,
      width: fill,
      height: fill,
      fill: fillColor,
      padding,
      borderRadius: 10,
    },
    child,
  );
}

function uiBubble(copy, user = false) {
  return row({ width: fill, height: hug, justify: user ? "end" : "start" }, [
    panel(
      {
        width: wrap(430),
        height: hug,
        padding: { x: 18, y: 12 },
        fill: user ? "#EAF0FF" : C.white,
        borderRadius: 12,
      },
      text(copy, {
        width: wrap(410),
        height: hug,
        style: { fontSize: 20, color: C.ink2 },
      }),
    ),
  ]);
}

function miniStatus(label, value, color) {
  return row({ width: fill, height: hug, gap: 10, align: "center" }, [
    shape({ geometry: "ellipse", width: fixed(11), height: fixed(11), fill: color }),
    text(label, { width: fixed(122), height: hug, style: { fontSize: 16, bold: true, color: C.ink2 } }),
    text(value, { width: fill, height: hug, style: { fontSize: 16, color: C.quiet } }),
  ]);
}

function uiMock() {
  return column({ name: "editable-ui-mock", width: fill, height: fill, gap: 16 }, [
    row({ width: fill, height: hug, justify: "between", align: "center" }, [
      text("🏠 兴享智家 · 慧家中枢", { width: hug, height: hug, style: { fontSize: 28, bold: true, color: C.ink } }),
      chip("自动闭环", C.teal),
    ]),
    text("端侧 Agent · 规则路由优先 · 本地小模型兜底 · SQLite 知识库", {
      width: fill,
      height: hug,
      style: { fontSize: 16, color: C.quiet },
    }),
    panel(
      { width: fill, height: fill, fill: "#F7FAFC", padding: { x: 22, y: 20 }, borderRadius: 14 },
      column({ width: fill, height: fill, gap: 14 }, [
        text("对话窗口", { width: fill, height: hug, style: { fontSize: 18, bold: true, color: C.violet } }),
        uiBubble("看看老人房现在怎么样？", true),
        uiBubble("老人房当前温度 17.5℃，湿度 60%，已 130 分钟无人活动。"),
        uiBubble("先保证爷爷那边。", true),
        uiBubble("已开启老人房视频优先策略，持续 60 分钟。"),
      ]),
    ),
    grid({ width: fill, height: hug, columns: [fr(1), fr(1)], columnGap: 16 }, [
      panel(
        { width: fill, height: hug, fill: "#F7FAFC", padding: { x: 18, y: 14 }, borderRadius: 12 },
        column({ width: fill, height: hug, gap: 8 }, [
          text("模型与意图", { width: fill, height: hug, style: { fontSize: 18, bold: true, color: C.teal } }),
          miniStatus("来源", "规则 / 本地 Qwen", C.teal),
          miniStatus("意图", "sensor_query", C.blue),
          miniStatus("耗时", "2 ms / 2070 ms", C.amber),
        ]),
      ),
      panel(
        { width: fill, height: hug, fill: "#F7FAFC", padding: { x: 18, y: 14 }, borderRadius: 12 },
        column({ width: fill, height: hug, gap: 8 }, [
          text("工具轨迹", { width: fill, height: hug, style: { fontSize: 18, bold: true, color: C.green } }),
          miniStatus("s1", "home_profile.query", C.green),
          miniStatus("s2", "sensor.query", C.green),
          miniStatus("s3", "device.query", C.green),
        ]),
      ),
    ]),
  ]);
}

function lane(label, note, color) {
  return column({ name: `lane-${label}`, width: fill, height: fill, gap: 14, justify: "center" }, [
    shape({ name: "lane-mark", width: fill, height: fixed(8), fill: color }),
    text(label, { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.ink } }),
    text(note, { width: fill, height: hug, style: { fontSize: 22, color: C.quiet } }),
  ]);
}

function step(label, note, color) {
  return column({ name: `step-${label}`, width: fill, height: hug, gap: 8, align: "center" }, [
    shape({ name: `step-mark-${label}`, geometry: "ellipse", width: fixed(108), height: fixed(108), fill: color }),
    text(label, {
      width: wrap(180),
      height: hug,
      align: "center",
      style: { fontSize: 22, bold: true, color },
    }),
    text(note, { width: wrap(260), height: hug, style: { fontSize: 18, color: C.ink2 }, align: "center" }),
  ]);
}

function apiItem(name, desc, color) {
  return row({ name: `api-${name}`, width: fill, height: hug, gap: 14, align: "center" }, [
    text(name, { width: fixed(220), height: hug, style: { fontSize: 24, bold: true, color } }),
    text(desc, { width: fill, height: hug, style: { fontSize: 22, color: C.ink2 } }),
  ]);
}

function apiItemLight(name, desc, color) {
  return row({ name: `api-light-${name}`, width: fill, height: hug, gap: 14, align: "center" }, [
    text(name, { width: fixed(220), height: hug, style: { fontSize: 24, bold: true, color } }),
    text(desc, { width: fill, height: hug, style: { fontSize: 22, color: "#D9E7E4" } }),
  ]);
}

function shortcutButton(label, color = C.teal) {
  return panel(
    {
      name: `shortcut-${label}`,
      width: fill,
      height: fixed(56),
      fill: "#F7FAFC",
      padding: { x: 12, y: 10 },
      borderRadius: 10,
    },
    row({ width: fill, height: fill, gap: 8, align: "center" }, [
      shape({ geometry: "ellipse", width: fixed(10), height: fixed(10), fill: color }),
      text(label, { width: fill, height: hug, style: { fontSize: 19, bold: true, color: C.ink2 } }),
    ]),
  );
}

function strategyOption(label, note, color, selected = false) {
  return panel(
    {
      name: `strategy-${label}`,
      width: fill,
      height: hug,
      fill: selected ? "#EEF8F5" : C.white,
      padding: { x: 20, y: 16 },
      borderRadius: 10,
    },
    row({ width: fill, height: hug, gap: 14, align: "start" }, [
      shape({ geometry: "ellipse", width: fixed(18), height: fixed(18), fill: selected ? color : "#D8E3DE" }),
      column({ width: fill, height: hug, gap: 6 }, [
        text(label, { width: fill, height: hug, style: { fontSize: 24, bold: true, color } }),
        text(note, { width: fill, height: hug, style: { fontSize: 18, color: C.quiet } }),
      ]),
    ]),
  );
}

function profileLine(member, details, color) {
  return row({ width: fill, height: hug, gap: 14, align: "start" }, [
    text(member, { width: fixed(90), height: hug, style: { fontSize: 24, bold: true, color } }),
    text(details, { width: fill, height: hug, style: { fontSize: 22, color: C.ink2 } }),
  ]);
}

function dagNode(id, toolName, note, color) {
  return panel(
    {
      name: `dag-${id}`,
      width: fill,
      height: fixed(150),
      fill: C.white,
      padding: { x: 18, y: 16 },
      borderRadius: 12,
    },
    column({ width: fill, height: fill, gap: 8, justify: "center" }, [
      text(id, { width: fill, height: hug, style: { fontSize: 18, bold: true, color } }),
      text(toolName, { width: fill, height: hug, style: { fontSize: 24, bold: true, color: C.ink } }),
      text(note, { width: fill, height: hug, style: { fontSize: 17, color: C.quiet } }),
    ]),
  );
}

function tableRow(cells, widths, fillColor = C.white, bold = false) {
  return panel(
    { width: fill, height: hug, fill: fillColor, padding: { x: 14, y: 10 }, borderRadius: 7 },
    row({ width: fill, height: hug, gap: 8, align: "center" }, cells.map((cell, idx) => (
      text(cell, {
        width: widths[idx],
        height: hug,
        style: { fontSize: bold ? 18 : 17, bold, color: bold ? C.ink : C.ink2 },
      })
    ))),
  );
}

function frameworkModule(name, desc, color, widthValue, heightValue = fixed(132), fillColor = C.white) {
  return panel(
    {
      name: `fw-${name}`,
      width: widthValue,
      height: heightValue,
      fill: fillColor,
      padding: { x: 12, y: 10 },
      borderRadius: 10,
    },
    column({ width: fill, height: fill, gap: 5, justify: "center", align: "center" }, [
      shape({ geometry: "ellipse", width: fixed(28), height: fixed(28), fill: color }),
      text(name, { width: fill, height: hug, align: "center", style: { fontSize: 19, bold: true, color: C.ink } }),
      text(desc, { width: fill, height: hug, align: "center", style: { fontSize: 14, color: C.ink2 } }),
    ]),
  );
}

function capabilityBox(name, desc, color) {
  return panel(
    {
      name: `cap-${name}`,
      width: fill,
      height: fixed(114),
      fill: C.white,
      padding: { x: 10, y: 9 },
      borderRadius: 9,
    },
    column({ width: fill, height: fill, gap: 4, justify: "center", align: "center" }, [
      shape({ geometry: "ellipse", width: fixed(22), height: fixed(22), fill: color }),
      text(name, { width: fill, height: hug, align: "center", style: { fontSize: 17, bold: true, color: C.ink } }),
      text(desc, { width: fill, height: hug, align: "center", style: { fontSize: 12, color: C.ink2 } }),
    ]),
  );
}

function legendItem(label, color) {
  return row({ width: hug, height: hug, gap: 8, align: "center" }, [
    rule({ width: fixed(52), stroke: color, weight: 4 }),
    text(label, { width: hug, height: hug, style: { fontSize: 18, color: C.ink2 } }),
  ]);
}

function alignCard(label, desc, impl, color, fillColor) {
  return panel(
    {
      name: `align-${label}`,
      width: fill,
      height: fill,
      fill: fillColor,
      padding: { x: 22, y: 18 },
      borderRadius: 10,
    },
    column({ width: fill, height: fill, gap: 10, justify: "center" }, [
      text(label, { width: fill, height: hug, style: { fontSize: 29, bold: true, color } }),
      text(desc, { width: fill, height: hug, style: { fontSize: 20, color: C.ink2 } }),
      rule({ width: fixed(120), stroke: color, weight: 3 }),
      text(impl, { width: fill, height: hug, style: { fontSize: 18, bold: true, color: C.ink } }),
    ]),
  );
}

function innovationLine(label, desc, color) {
  return row({ width: fill, height: hug, gap: 14, align: "start" }, [
    shape({ geometry: "ellipse", width: fixed(13), height: fixed(13), fill: color }),
    column({ width: fill, height: hug, gap: 4 }, [
      text(label, { width: fill, height: hug, style: { fontSize: 22, bold: true, color } }),
      text(desc, { width: fill, height: hug, style: { fontSize: 18, color: C.ink2 } }),
    ]),
  ]);
}

function scoreCard(label, desc, evidence, color, fillColor) {
  return panel(
    {
      name: `score-${label}`,
      width: fill,
      height: fill,
      fill: fillColor,
      padding: { x: 22, y: 18 },
      borderRadius: 10,
    },
    column({ width: fill, height: fill, gap: 10, justify: "center" }, [
      row({ width: fill, height: hug, justify: "between", align: "center" }, [
        text(label, { width: hug, height: hug, style: { fontSize: 31, bold: true, color } }),
        text("20 分", { width: hug, height: hug, style: { fontSize: 21, bold: true, color: C.quiet } }),
      ]),
      text(desc, { width: fill, height: hug, style: { fontSize: 20, color: C.ink2 } }),
      rule({ width: fixed(140), stroke: color, weight: 3 }),
      text(evidence, { width: fill, height: hug, style: { fontSize: 18, bold: true, color: C.ink } }),
    ]),
  );
}

// 1. Cover
addSlide(
  "cover",
  C.cloud,
  row({ width: fill, height: fill, padding: { x: 92, y: 70 }, gap: 58, align: "center" }, [
    column({ width: fill, height: fill, justify: "between" }, [
      row({ width: fill, height: hug, justify: "between", align: "center" }, [
        text("复赛作品展示", { width: hug, height: hug, style: { fontSize: 22, bold: true, color: C.teal } }),
        text("西安电子科技大学广州研究院", { width: hug, height: hug, style: { fontSize: 20, color: C.quiet } }),
      ]),
      column({ width: fill, height: hug, gap: 26 }, [
        text("兴享智家", { name: "cover-main", width: wrap(760), height: hug, style: { fontSize: 96, bold: true, color: C.ink } }),
        text("慧家中枢", { width: wrap(620), height: hug, style: { fontSize: 70, bold: true, color: C.teal } }),
        rule({ width: fixed(320), stroke: C.amber, weight: 5 }),
        text("面向三代同堂家庭的本地家庭中枢：用自然语言统一调度老人关怀、睡前联动、网络 QoS、主动巡检与安全确认。", {
          width: wrap(900),
          height: hug,
          style: { fontSize: 30, color: C.ink2 },
        }),
      ]),
      row({ width: fill, height: hug, gap: 12 }, [
        chip("端侧 Agent", C.teal),
        chip("本地 Qwen", C.blue),
        chip("工具闭环", C.green),
        chip("SQLite 记忆", C.amber),
      ]),
    ]),
    panel(
      {
        name: "cover-ui-device",
        width: fixed(680),
        height: fixed(850),
        fill: "#F4F7F8",
        padding: { x: 18, y: 18 },
        borderRadius: 28,
      },
      uiMock(),
    ),
  ]),
);

// 2. Pain points
addSlide(
  "pain",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 88, y: 68 }, justify: "between", gap: 34 }, [
    title("家庭智能化的核心挑战", "家庭智能服务的关键难点在于多设备协同、网络状态理解、关怀任务上下文和本地隐私保护。"),
    grid({ width: fill, height: fill, columns: [fr(1), fr(1), fr(1), fr(1)], columnGap: 32 }, [
      lane("设备割裂", "灯、空调、门锁、摄像头、路由器分散在多个入口。", C.teal),
      lane("网络难定位", "Wi‑Fi 卡顿、Mesh 信号、带宽占用对普通家庭不透明。", C.blue),
      lane("关怀弱上下文", "提醒工具知道时间，却不知道家庭状态和上一轮任务。", C.amber),
      lane("隐私有顾虑", "作息、健康提醒、摄像头与网络日志不适合默认上云。", C.coral),
    ]),
    footer(2),
  ]),
);

// 3. Positioning
addSlide(
  "position",
  C.cloud,
  column({ width: fill, height: fill, padding: { x: 92, y: 70 }, justify: "between", gap: 30 }, [
    title("产品定位：面向三代同堂家庭的本地任务中枢", "系统运行在家庭网关或边缘盒子上，把家庭成员、房间、设备、网络和提醒组织为可执行任务。"),
    row({ width: fill, height: fill, gap: 52, align: "center" }, [
      column({ width: fill, height: fill, justify: "center", gap: 20 }, [
        text("核心价值", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        text("用户说一句家庭语言，系统完成理解、规划、工具调用、状态更新和结果解释。", {
          width: wrap(780),
          height: hug,
          style: { fontSize: 42, bold: true, color: C.ink },
        }),
        text("核心能力围绕四类家庭任务展开：老人关怀、睡前联动、网络 QoS、主动巡检。", {
          width: wrap(760),
          height: hug,
          style: { fontSize: 24, color: C.quiet },
        }),
      ]),
      grid({ width: fill, height: hug, columns: [fr(1), fr(1)], rows: [auto, auto], columnGap: 22, rowGap: 22 }, [
        plainPanel("target-user", column({ width: fill, height: hug, gap: 10 }, [
          text("家庭成员", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.teal } }),
          text("自然语言控制、查询状态、处理日常提醒。", { width: fill, height: hug, style: { fontSize: 21, color: C.ink2 } }),
        ]), C.white),
        plainPanel("target-elder", column({ width: fill, height: hug, gap: 10 }, [
          text("老年人", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.amber } }),
          text("吃药、饮水、休息、异常未响应等关怀。", { width: fill, height: hug, style: { fontSize: 21, color: C.ink2 } }),
        ]), C.white),
        plainPanel("target-admin", column({ width: fill, height: hug, gap: 10 }, [
          text("家庭管理员", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.blue } }),
          text("设备、网络、能耗、提醒和安全状态统一可视。", { width: fill, height: hug, style: { fontSize: 21, color: C.ink2 } }),
        ]), C.white),
        plainPanel("target-vendor", column({ width: fill, height: hug, gap: 10 }, [
          text("终端厂商", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.green } }),
          text("可集成到家庭网关、智能屏、路由器、机器人。", { width: fill, height: hug, style: { fontSize: 21, color: C.ink2 } }),
        ]), C.white),
      ]),
    ]),
    footer(3),
  ]),
);

// 4. Contest capability and innovation alignment
addSlide(
  "contest-alignment",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 80, y: 62 }, justify: "between", gap: 24 }, [
    title("赛题能力与创新方向对齐", "作品选择家庭场景，在端侧算力约束下实现可运行、可解释、可演示的场景化智能体系统。"),
    row({ width: fill, height: fill, gap: 34, align: "stretch" }, [
      column({ width: fill, height: fill, gap: 18 }, [
        text("四项核心能力", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        grid({ width: fill, height: fill, columns: [fr(1), fr(1)], rows: [fr(1), fr(1)], columnGap: 18, rowGap: 18 }, [
          alignCard("场景理解与任务规划", "理解家庭自然语言指令，将其转为可执行任务流程。", "Router + 本地 Qwen + TaskPlanner DAG", C.teal, "#EEF8F5"),
          alignCard("工具调用与资源整合", "统一调用设备、网络、提醒、知识、画像和安全工具。", "ToolRegistry 白名单工具 + PlanExecutor", C.blue, "#EEF4FF"),
          alignCard("多轮对话与状态保持", "保持成员、房间、上一轮任务、待确认动作等上下文。", "Session State + SQLite 长期家庭画像", C.amber, "#FFF8E8"),
          alignCard("高效推理与实时响应", "有限算力下采用规则优先与量化小模型兜底。", "规则毫秒级路径 + Qwen2.5-1.5B Q4_K_M", C.green, "#EFF8F2"),
        ]),
      ]),
      plainPanel("innovation-alignment", column({ width: fill, height: fill, gap: 18 }, [
        text("创新方向落地", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.violet } }),
        innovationLine("轻量模型意图理解与槽位填充", "本地 Qwen 输出结构化 intent、confidence、slots，用于规则未命中的补识别。", C.blue),
        innovationLine("端侧 Agent 架构与任务规划", "main.run 统一入口串联 Pipeline、Router、Planner、Executor、ToolRegistry。", C.teal),
        innovationLine("多源场景感知", "传感器、设备、网络、提醒和家庭画像共同形成家庭状态视图。", C.green),
        innovationLine("模型量化与低资源部署", "Qwen2.5-1.5B-Instruct Q4_K_M GGUF 适配家庭网关/边缘盒子。", C.amber),
        innovationLine("本地知识库与检索增强", "SQLite 保存知识库和家庭规则；无可信命中时不编造。", C.violet),
        innovationLine("低资源持续适应", "长期画像随对话更新，让系统逐步适应家庭成员偏好。", C.coral),
      ]), C.white),
    ]),
    panel(
      { width: fill, height: hug, fill: C.darkBg, padding: { x: 28, y: 18 }, borderRadius: 10 },
      text("一句话对齐赛题：在家庭场景中，用端侧轻量模型 + 可控工具链 + 本地状态记忆，完成从理解到执行的智能体闭环。", {
        width: fill,
        height: hug,
        align: "center",
        style: { fontSize: 28, bold: true, color: C.white },
      }),
    ),
    footer(4),
  ]),
);

// 5. Scoring dimensions
addSlide(
  "score-alignment",
  C.cloud,
  column({ width: fill, height: fill, padding: { x: 80, y: 62 }, justify: "between", gap: 26 }, [
    title("评分维度对齐：五项指标都有可展示证据", "围绕创新、价值、成本、演示和文档五个 20 分维度组织讲述，让作品能力和评分点直接对应。"),
    grid({ width: fill, height: fill, columns: [fr(1), fr(1), fr(1)], rows: [fr(1), fr(1)], columnGap: 22, rowGap: 22 }, [
      scoreCard("创新", "从通用问答升级为家庭端侧任务中枢，结合轻量模型、工具规划、长期画像和本地知识。", "重点页：能力创新对齐、整体框架、Agent 主链路", C.violet, "#F1EFFF"),
      scoreCard("价值", "面向三代同堂家庭的真实痛点：老人关怀、睡前联动、网络诊断、主动巡检。", "重点页：产品定位、核心场景、一个晚上里的体验", C.teal, "#EEF8F5"),
      scoreCard("成本", "规则优先降低推理开销，本地量化 Qwen 只在不确定时参与，数据留在 SQLite。", "重点页：端侧可信、模型策略、性能指标", C.green, "#EFF8F2"),
      scoreCard("演示", "有可运行 Web Demo，能看到快捷场景、意图、DAG、工具日志、设备和传感器状态。", "重点页：演示界面、功能展示一至四", C.blue, "#EEF4FF"),
      scoreCard("文档", "方案文档、接口文档、技术说明、PPT 与 Demo 口径一致，能追溯到代码模块。", "重点页：接口契约、工具注册表、状态记忆、框架图", C.amber, "#FFF8E8"),
      panel(
        { name: "score-sum", width: fill, height: fill, fill: C.darkBg, padding: { x: 26, y: 24 }, borderRadius: 10 },
        column({ width: fill, height: fill, gap: 14, justify: "center" }, [
          text("总分逻辑", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.white } }),
          text("每个评分维度都对应可讲的产品价值、可看的 Demo 页面、可追踪的工程实现和可验证的本地运行证据。", {
            width: fill,
            height: hug,
            style: { fontSize: 22, color: "#D9E7E4" },
          }),
        ]),
      ),
    ]),
    footer(5),
  ]),
);

// 6. Core scenarios
addSlide(
  "scenarios",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 82, y: 66 }, justify: "between", gap: 32 }, [
    title("核心场景能力：四类家庭任务闭环", "自然语言进入规划与执行，过程呈现意图、DAG 与工具日志"),
    grid({ width: fill, height: fill, columns: [fr(1), fr(1), fr(1), fr(1)], columnGap: 24 }, [
      plainPanel("scene-elder", column({ width: fill, height: fill, gap: 18 }, [
        text("老人关怀", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        text("吃药提醒\n完成/取消\n未响应复提醒\n老人房状态", { width: fill, height: hug, style: type.body }),
        text("工具：reminder.* / sensor.query", { width: fill, height: hug, style: type.small }),
      ]), "#EEF8F5"),
      plainPanel("scene-sleep", column({ width: fill, height: fill, gap: 18 }, [
        text("睡前联动", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.amber } }),
        text("关电视\n调暗灯光\n空调睡眠\n检查门锁", { width: fill, height: hug, style: type.body }),
        text("工具：scene.apply / device.query", { width: fill, height: hug, style: type.small }),
      ]), "#FFF8E8"),
      plainPanel("scene-net", column({ width: fill, height: fill, gap: 18 }, [
        text("网络 QoS", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.blue } }),
        text("视频卡顿诊断\nMesh 信号\n带宽占用\n老人优先", { width: fill, height: hug, style: type.body }),
        text("工具：network.diagnose / apply_qos", { width: fill, height: hug, style: type.small }),
      ]), "#EEF4FF"),
      plainPanel("scene-safe", column({ width: fill, height: fill, gap: 18 }, [
        text("主动巡检", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.green } }),
        text("全屋传感器\n低温/久未活动\n异常提示\n安全确认", { width: fill, height: hug, style: type.body }),
        text("工具：sensor.* / safety.check", { width: fill, height: hug, style: type.small }),
      ]), "#EFF8F2"),
    ]),
    footer(6),
  ]),
);

// 7. User journey
addSlide(
  "journey",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 86, y: 68 }, justify: "between", gap: 34 }, [
    title("一个晚上里的产品体验", "将核心能力组织到家庭时间线中，形成围绕家庭日常的持续服务体验。"),
    row({ width: fill, height: hug, gap: 26, align: "start" }, [
      step("19:30", "孩子学习模式：灯光护眼，45 分钟后休息提醒", C.violet),
      text("→", { width: hug, height: fixed(132), style: { fontSize: 46, bold: true, color: C.quiet2 } }),
      step("20:30", "老人房视频卡顿：诊断并开启老人房 QoS", C.blue),
      text("→", { width: hug, height: fixed(132), style: { fontSize: 46, bold: true, color: C.quiet2 } }),
      step("21:00", "爷爷吃药提醒：未回应 10 分钟后再次提醒", C.amber),
      text("→", { width: hug, height: fixed(132), style: { fontSize: 46, bold: true, color: C.quiet2 } }),
      step("22:30", "睡前模式：设备联动、门锁检查、老人状态确认", C.teal),
      text("→", { width: hug, height: fixed(132), style: { fontSize: 46, bold: true, color: C.quiet2 } }),
      step("夜间", "主动巡检：低温、长时间无活动、安全异常提示", C.green),
    ]),
    panel(
      { width: fill, height: hug, padding: { x: 34, y: 26 }, fill: C.mist, borderRadius: 12 },
      text("产品体验：同一套 Agent 能跨越成员、房间、设备、网络、提醒和知识，减少多个 App 之间的切换。", {
        width: fill,
        height: hug,
        style: { fontSize: 30, bold: true, color: C.ink },
      }),
    ),
    footer(7),
  ]),
);

// 8. Product surface
addSlide(
  "surface",
  C.cloud,
  row({ width: fill, height: fill, padding: { x: 82, y: 62 }, gap: 48, align: "center" }, [
    panel(
      { width: fixed(720), height: fixed(900), fill: C.white, padding: { x: 14, y: 14 }, borderRadius: 26 },
      uiMock(),
    ),
    column({ width: fill, height: fill, justify: "between", gap: 28 }, [
      title("演示界面：智能体过程可见", "界面围绕智能体运行过程设计，让用户能够看到每轮请求的理解、执行和状态变化。"),
      column({ width: fill, height: fill, gap: 18, justify: "center" }, [
        bullet("对话窗口：用户自然语言和最终解释回复。"),
        bullet("运行策略：自动闭环、规则调试、强制模型识别调试。", C.blue),
        bullet("意图来源：规则或本地模型，置信度和理由可见。", C.teal),
        bullet("任务规划 DAG：展示任务拆解和依赖关系。", C.amber),
        bullet("工具日志：展示每个工具的参数、耗时和结果。", C.green),
        bullet("长期画像：家庭成员偏好随对话持久更新。", C.coral),
      ]),
      footer(8),
    ]),
  ]),
);

// 9. Demo feature: shortcuts and model strategy
addSlide(
  "demo-shortcuts",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 82, y: 64 }, justify: "between", gap: 26 }, [
    title("功能展示一：快捷场景与运行策略", "Demo 首页不是静态展示板，快捷按钮会把真实指令送入同一个 run 入口；运行策略用于现场对比规则路径与本地模型路径。"),
    row({ width: fill, height: fill, gap: 36, align: "stretch" }, [
      plainPanel("shortcut-surface", column({ width: fill, height: fill, gap: 20 }, [
        row({ width: fill, height: hug, justify: "between", align: "center" }, [
          text("🎯 快捷场景", { width: hug, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
          chip("真实输入模板", C.blue),
        ]),
        panel(
          { width: fill, height: hug, fill: "#F7FAFC", padding: { x: 18, y: 14 }, borderRadius: 10 },
          text("例如：爷爷房间视频有点卡，帮我看看。", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2 } }),
        ),
        grid({ width: fill, height: hug, columns: [fr(1), fr(1)], rows: [auto, auto, auto, auto, auto], columnGap: 14, rowGap: 12 }, [
          shortcutButton("睡前模式", C.teal),
          shortcutButton("离家模式", C.coral),
          shortcutButton("观影模式", C.violet),
          shortcutButton("网络诊断", C.blue),
          shortcutButton("老人巡检", C.green),
          shortcutButton("一键巡检", C.green),
          shortcutButton("儿童学习", C.violet),
          shortcutButton("能耗查询", C.amber),
          shortcutButton("吃药提醒", C.amber),
          shortcutButton("敏感动作", C.coral),
        ]),
        text("展示价值：一键触发主线场景，避免现场反复输入长句；每个按钮背后仍走完整 Agent 流程。", {
          width: fill,
          height: hug,
          style: { fontSize: 22, bold: true, color: C.ink2 },
        }),
      ]), C.white),
      column({ width: fixed(720), height: fill, gap: 18 }, [
        strategyOption("自动闭环（推荐）", "规则优先；规则不确定时调用本地 Qwen 补识别，识别后继续走工具。", C.teal, true),
        strategyOption("规则仅调试（关闭模型）", "用于展示低延迟规则路径，也能证明没有模型时核心场景仍可运行。", C.blue),
        strategyOption("调试：强制模型识别（仍走工具）", "用于现场稳定触发 local_llm，展示模型参与但最终回复来自工具结果。", C.violet),
        panel(
          { width: fill, height: fill, fill: C.mist, padding: { x: 26, y: 24 }, borderRadius: 12 },
          column({ width: fill, height: fill, gap: 16, justify: "center" }, [
            text("策略设计", { width: fill, height: hug, style: { fontSize: 32, bold: true, color: C.teal } }),
            bullet("同一个问题可对比规则、本地模型、自动闭环三种路径。"),
            bullet("本地模型只负责补识别或直接回答兜底，家庭任务仍由工具执行。", C.blue),
            bullet("右侧会同步展示意图来源、模型耗时和是否降级。", C.amber),
          ]),
        ),
      ]),
    ]),
    footer(9),
  ]),
);

// 10. Demo feature: memory and profile
addSlide(
  "demo-memory",
  C.cloud,
  column({ width: fill, height: fill, padding: { x: 82, y: 64 }, justify: "between", gap: 26 }, [
    title("功能展示二：长期记忆与家庭画像", "长期画像区域会随着对话持久更新，系统能记住家庭成员的偏好、饮食限制和照护习惯。"),
    row({ width: fill, height: fill, gap: 36, align: "stretch" }, [
      plainPanel("memory-chat", column({ width: fill, height: fill, gap: 18 }, [
        text("对话触发记忆写入", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        uiBubble("记住奶奶喜欢吃番茄炒蛋", true),
        uiBubble("已记住奶奶的饮食偏好：喜欢番茄炒蛋。"),
        uiBubble("中午吃什么好？", true),
        uiBubble("可以优先考虑番茄炒蛋，口味清淡，比较符合奶奶偏好。"),
        panel(
          { width: fill, height: hug, fill: "#FFF8E8", padding: { x: 18, y: 14 }, borderRadius: 10 },
          text("这类回答会读取长期画像，不只是依赖上一轮聊天上下文。", { width: fill, height: hug, style: { fontSize: 22, bold: true, color: C.ink2 } }),
        ),
      ]), C.white),
      plainPanel("profile-panel", column({ width: fill, height: fill, gap: 18 }, [
        row({ width: fill, height: hug, justify: "between", align: "center" }, [
          text("🧠 长期家庭画像", { width: hug, height: hug, style: { fontSize: 34, bold: true, color: C.amber } }),
          chip("SQLite 持久化", C.green),
        ]),
        profileLine("奶奶", "爱好：喜欢看电影；饮食：喜欢吃软一点的面条、喜欢吃香菜、喜欢吃番茄炒蛋", C.amber),
        profileLine("爷爷", "性格：节俭；饮食：不吃辣、喜欢清淡；爱好：散步", C.teal),
        profileLine("孩子", "爱好：喜欢画画、喜欢恐龙、喜欢奶龙玩具；饮食：喜欢吃番茄炒蛋", C.violet),
        profileLine("爸爸", "爱好：喜欢跑步；饮食：喜欢吃牛肉面", C.blue),
        rule({ width: fill, stroke: C.line, weight: 2 }),
        row({ width: fill, height: hug, gap: 16, align: "center" }, [
          dagNode("s1", "profile.remember", "抽取成员与偏好", C.teal),
          text("→", { width: hug, height: hug, style: { fontSize: 34, bold: true, color: C.quiet2 } }),
          dagNode("s2", "family_profiles", "写入本地 SQLite", C.green),
          text("→", { width: hug, height: hug, style: { fontSize: 34, bold: true, color: C.quiet2 } }),
          dagNode("s3", "前端刷新", "画像面板实时更新", C.amber),
        ]),
      ]), C.white),
    ]),
    footer(10),
  ]),
);

// 11. Demo feature: intent and planning
addSlide(
  "demo-intent-plan",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 82, y: 64 }, justify: "between", gap: 26 }, [
    title("功能展示三：意图识别与任务规划 DAG", "每轮请求都会展示意图来源、置信度、槽位和规划步骤，能解释系统为什么调用这些工具。"),
    row({ width: fill, height: fill, gap: 36, align: "stretch" }, [
      plainPanel("intent-panel", column({ width: fill, height: fill, gap: 18 }, [
        text("意图识别面板", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        tableRow(["字段", "示例值"], [fixed(150), fill], "#EEF8F5", true),
        tableRow(["用户输入", "爷爷房间视频有点卡，帮我看看。"], [fixed(150), fill]),
        tableRow(["意图", "network_qos / network_diagnosis"], [fixed(150), fill]),
        tableRow(["来源", "规则命中；或本地 Qwen 补识别"], [fixed(150), fill]),
        tableRow(["置信度", "0.90 - 0.96"], [fixed(150), fill]),
        tableRow(["槽位", "{ room: 老人房, member: 爷爷 }"], [fixed(150), fill]),
        panel(
          { width: fill, height: fill, fill: C.mist, padding: { x: 22, y: 20 }, borderRadius: 12 },
          column({ width: fill, height: fill, gap: 14, justify: "center" }, [
            text("本地模型参与点", { width: fill, height: hug, style: { fontSize: 28, bold: true, color: C.blue } }),
            text("当规则没有稳定命中时，本地 Qwen 输出结构化 JSON 意图；只要识别到可执行家庭任务，后续仍进入 Planner 和工具链。", {
              width: fill,
              height: hug,
              style: { fontSize: 22, color: C.ink2 },
            }),
          ]),
        ),
      ]), C.white),
      plainPanel("dag-panel", column({ width: fill, height: fill, gap: 20 }, [
        text("任务规划 (DAG)", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.amber } }),
        row({ width: fill, height: hug, gap: 14, align: "center" }, [
          dagNode("s1", "home_profile.query", "读取老人房与成员上下文", C.teal),
          text("→", { width: hug, height: hug, style: { fontSize: 34, bold: true, color: C.quiet2 } }),
          dagNode("s2", "network.diagnose", "读取 Mesh、RSSI、带宽占用", C.blue),
        ]),
        row({ width: fill, height: hug, gap: 14, align: "center" }, [
          dagNode("s3", "network.apply_qos", "为老人房视频开启优先级", C.green),
          text("→", { width: hug, height: hug, style: { fontSize: 34, bold: true, color: C.quiet2 } }),
          dagNode("s4", "reply.build", "汇总工具结果生成回复", C.coral),
        ]),
        panel(
          { width: fill, height: fill, fill: "#FFF8E8", padding: { x: 22, y: 20 }, borderRadius: 12 },
          column({ width: fill, height: fill, gap: 12, justify: "center" }, [
            text("为什么要展示 DAG", { width: fill, height: hug, style: { fontSize: 28, bold: true, color: C.amber } }),
            bullet("证明系统不是直接吐固定话术，而是先拆任务再执行。"),
            bullet("敏感动作和依赖关系能在计划层被拦截和确认。", C.coral),
            bullet("每个步骤都能追到对应工具、入参、依赖和耗时。", C.green),
          ]),
        ),
      ]), C.white),
    ]),
    footer(11),
  ]),
);

// 12. Demo feature: tools and state panels
addSlide(
  "demo-tools-state",
  C.cloud,
  column({ width: fill, height: fill, padding: { x: 82, y: 64 }, justify: "between", gap: 26 }, [
    title("功能展示四：工具日志、设备状态与传感器面板", "右侧面板把执行结果展开为可检查的日志和状态表，展示系统已经接入本地模拟设备与传感器状态。"),
    row({ width: fill, height: fill, gap: 32, align: "stretch" }, [
      plainPanel("tool-log-panel", column({ width: fill, height: fill, gap: 16 }, [
        text("🔧 工具调用日志", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.green } }),
        tableRow(["步骤", "工具", "结果", "耗时"], [fixed(72), fixed(240), fill, fixed(92)], "#EFF8F2", true),
        tableRow(["s1", "home_profile.query", "读取爷爷与老人房画像", "1 ms"], [fixed(72), fixed(240), fill, fixed(92)]),
        tableRow(["s2", "sensor.query", "老人房温度 17.5℃，湿度 60%", "2 ms"], [fixed(72), fixed(240), fill, fixed(92)]),
        tableRow(["s3", "device.query", "老人房灯、空调已读取", "1 ms"], [fixed(72), fixed(240), fill, fixed(92)]),
        tableRow(["s4", "network.apply_qos", "已开启老人房视频优先", "4 ms"], [fixed(72), fixed(240), fill, fixed(92)]),
        panel(
          { width: fill, height: fill, fill: C.mist, padding: { x: 22, y: 18 }, borderRadius: 12 },
          column({ width: fill, height: fill, gap: 10, justify: "center" }, [
            text("性能指标", { width: fill, height: hug, style: { fontSize: 28, bold: true, color: C.teal } }),
            text("总耗时、模型耗时、工具耗时和是否命中缓存会在底部同步更新。", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2 } }),
          ]),
        ),
      ]), C.white),
      column({ width: fixed(820), height: fill, gap: 20 }, [
        plainPanel("device-panel", column({ width: fill, height: fill, gap: 14 }, [
          text("💡 设备状态面板", { width: fill, height: hug, style: { fontSize: 32, bold: true, color: C.amber } }),
          tableRow(["房间", "设备", "状态", "详情"], [fixed(150), fixed(210), fixed(90), fill], "#FFF8E8", true),
          tableRow(["客厅", "客厅灯", "开启", "亮度 60%"], [fixed(150), fixed(210), fixed(90), fill]),
          tableRow(["主卧", "主卧空调", "开启", "26℃，睡眠模式"], [fixed(150), fixed(210), fixed(90), fill]),
          tableRow(["老人房", "老人房空调", "开启", "24℃，舒适模式"], [fixed(150), fixed(210), fixed(90), fill]),
          tableRow(["玄关", "门锁", "锁定", "敏感动作需确认"], [fixed(150), fixed(210), fixed(90), fill]),
        ]), C.white),
        plainPanel("sensor-panel", column({ width: fill, height: fill, gap: 14 }, [
          text("🌡 传感器面板", { width: fill, height: hug, style: { fontSize: 32, bold: true, color: C.blue } }),
          tableRow(["房间", "温度", "湿度", "活动", "噪声"], [fixed(150), fixed(110), fixed(110), fill, fixed(100)], "#EEF4FF", true),
          tableRow(["老人房", "17.5℃", "60%", "130 分钟无人活动", "低"], [fixed(150), fixed(110), fixed(110), fill, fixed(100)]),
          tableRow(["儿童房", "24.0℃", "52%", "学习中", "中"], [fixed(150), fixed(110), fixed(110), fill, fixed(100)]),
          tableRow(["客厅", "25.0℃", "55%", "有人活动", "中"], [fixed(150), fixed(110), fixed(110), fill, fixed(100)]),
        ]), C.white),
      ]),
    ]),
    footer(12),
  ]),
);

// 13. Interface contract
addSlide(
  "interface",
  C.cloud,
  column({ width: fill, height: fill, padding: { x: 84, y: 66 }, justify: "between", gap: 30 }, [
    title("接口契约：一个 run 入口承载完整智能体闭环", "接口文档围绕比赛规定的 main.run 设计，命令行、Web Demo、测试脚本都复用同一个入口。"),
    row({ width: fill, height: fill, gap: 34, align: "stretch" }, [
      plainPanel("run-input", column({ width: fill, height: fill, gap: 20 }, [
        text("输入", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        text("user_input: 自然语言\nstate: 会话与家庭状态\nconfig: 模型、确认、安全、调试配置", {
          width: fill,
          height: hug,
          style: type.body,
        }),
      ]), C.white),
      column({ width: fixed(120), height: fill, justify: "center", align: "center" }, [
        text("run()", { width: hug, height: hug, style: { fontSize: 34, bold: true, color: C.amber } }),
        rule({ width: fixed(5), height: fixed(260), stroke: C.amber, weight: 5 }),
      ]),
      plainPanel("run-output", column({ width: fill, height: fill, gap: 13 }, [
        text("输出", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
        apiItem("reply", "面向用户的自然语言回复", C.teal),
        apiItem("intent", "意图、置信度、槽位、来源", C.blue),
        apiItem("plan", "DAG 任务步骤和依赖关系", C.amber),
        apiItem("tool_results", "结构化工具调用结果", C.green),
        apiItem("state", "更新后的会话与家庭状态", C.violet),
        apiItem("metrics", "总耗时、模型耗时、工具耗时、内存估计", C.coral),
        apiItem("safety", "敏感动作确认状态", C.teal),
      ]), C.white),
    ]),
    footer(13),
  ]),
);

// 14. Overall project framework
addSlide(
  "project-framework",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 34, y: 26 }, justify: "between", gap: 12 }, [
    panel(
      { width: fill, height: fixed(178), fill: "#F3F8FF", padding: { x: 28, y: 18 }, borderRadius: 12 },
      row({ width: fill, height: fill, gap: 24, align: "center" }, [
        column({ width: fixed(245), height: fill, justify: "center", gap: 12 }, [
          text("交互层", { width: fill, height: hug, style: { fontSize: 38, bold: true, color: C.blue } }),
          text("真实可用的前端入口\n支持多种触发方式", { width: fill, height: hug, style: { fontSize: 21, color: C.ink2 } }),
        ]),
        panel(
          { width: fill, height: fixed(132), fill: C.white, padding: { x: 26, y: 10 }, borderRadius: 12 },
          row({ width: fill, height: fill, gap: 16, align: "center", justify: "center" }, [
            frameworkModule("用户", "自然语言输入", C.blue, fixed(140), fixed(104), "#F7FAFC"),
            text("→", { width: hug, height: hug, style: { fontSize: 36, bold: true, color: C.blue } }),
            frameworkModule("快捷场景", "一键触发主线", C.blue, fixed(160), fixed(104), "#F7FAFC"),
            text("→", { width: hug, height: hug, style: { fontSize: 36, bold: true, color: C.blue } }),
            frameworkModule("Gradio Demo 界面", "过程可视化", C.blue, fixed(220), fixed(104), "#F7FAFC"),
            text("→", { width: hug, height: hug, style: { fontSize: 36, bold: true, color: C.blue } }),
            frameworkModule("main.run", "统一入口", C.blue, fixed(160), fixed(104), "#F7FAFC"),
          ]),
        ),
      ]),
    ),
    panel(
      { width: fill, height: fixed(238), fill: "#FFF8EC", padding: { x: 28, y: 18 }, borderRadius: 12 },
      row({ width: fill, height: fill, gap: 24, align: "center" }, [
        column({ width: fixed(245), height: fill, justify: "center", gap: 12 }, [
          text("Agent 主链路", { width: fill, height: hug, style: { fontSize: 36, bold: true, color: "#CF6200" } }),
          text("端侧 Agent 执行闭环\n完成理解、规划、执行、回复", { width: fill, height: hug, style: { fontSize: 20, color: C.ink2 } }),
        ]),
        row({ width: fill, height: fill, gap: 10, align: "center", justify: "center" }, [
          frameworkModule("Pipeline", "主流程编排", "#D66A00", fixed(152), fixed(150), C.white),
          text("→", { width: hug, height: hug, style: { fontSize: 30, bold: true, color: "#D66A00" } }),
          frameworkModule("Router", "规则优先", "#D66A00", fixed(152), fixed(150), C.white),
          text("→", { width: hug, height: hug, style: { fontSize: 30, bold: true, color: "#D66A00" } }),
          frameworkModule("本地 Qwen", "意图识别兜底", "#D66A00", fixed(152), fixed(150), C.white),
          text("→", { width: hug, height: hug, style: { fontSize: 30, bold: true, color: "#D66A00" } }),
          frameworkModule("Planner", "生成执行计划", "#D66A00", fixed(152), fixed(150), C.white),
          text("→", { width: hug, height: hug, style: { fontSize: 30, bold: true, color: "#D66A00" } }),
          frameworkModule("Executor", "按计划调度", "#D66A00", fixed(152), fixed(150), C.white),
          text("→", { width: hug, height: hug, style: { fontSize: 30, bold: true, color: "#D66A00" } }),
          frameworkModule("ToolRegistry", "统一管理", "#D66A00", fixed(152), fixed(150), C.white),
          text("→", { width: hug, height: hug, style: { fontSize: 30, bold: true, color: "#D66A00" } }),
          frameworkModule("Reply Builder", "结果整合", "#D66A00", fixed(152), fixed(150), C.white),
        ]),
      ]),
    ),
    panel(
      { width: fill, height: fixed(420), fill: "#F3FAF4", padding: { x: 28, y: 18 }, borderRadius: 12 },
      row({ width: fill, height: fill, gap: 24, align: "center" }, [
        column({ width: fixed(245), height: fill, justify: "center", gap: 12 }, [
          text("本地能力层", { width: fill, height: hug, style: { fontSize: 36, bold: true, color: C.green } }),
          text("端侧工具与数据闭环\n所有能力与数据均在本地", { width: fill, height: hug, style: { fontSize: 20, color: C.ink2 } }),
        ]),
        column({ width: fill, height: fill, gap: 14, justify: "center" }, [
          row({ width: fill, height: hug, justify: "between", align: "center" }, [
            text("ToolRegistry 调用本地能力", { width: hug, height: hug, style: { fontSize: 22, bold: true, color: C.green } }),
            text("能力调用与数据流回到 State / SQLite，再由 Reply Builder 汇总回复", { width: hug, height: hug, style: { fontSize: 17, color: C.quiet } }),
          ]),
          grid({ width: fill, height: hug, columns: [fr(1), fr(1), fr(1), fr(1), fr(1), fr(1), fr(1), fr(1)], columnGap: 12 }, [
            capabilityBox("传感器", "温湿度、活动\n人体感知", C.green),
            capabilityBox("设备控制", "查询、控制\n状态管理", C.green),
            capabilityBox("场景联动", "场景创建\n联动控制", C.green),
            capabilityBox("网络诊断", "Mesh / QoS\n故障诊断", C.green),
            capabilityBox("提醒管理", "创建、完成\n取消提醒", C.green),
            capabilityBox("长期画像", "偏好记忆\n习惯建模", C.green),
            capabilityBox("知识库", "本地知识检索\n问答支持", C.green),
            capabilityBox("安全确认", "危险操作确认\n安全策略校验", C.green),
          ]),
          row({ width: fill, height: hug, gap: 28, align: "center", justify: "center" }, [
            panel(
              { width: fixed(520), height: fixed(110), fill: C.white, padding: { x: 24, y: 18 }, borderRadius: 12 },
              row({ width: fill, height: fill, gap: 18, align: "center" }, [
                shape({ geometry: "ellipse", width: fixed(52), height: fixed(52), fill: C.green }),
                column({ width: fill, height: hug, gap: 6 }, [
                  text("SQLite", { width: fill, height: hug, style: { fontSize: 28, bold: true, color: C.ink } }),
                  text("家庭画像库 / 知识库 / 配置数据\n本地存储，隐私安全", { width: fill, height: hug, style: { fontSize: 17, color: C.ink2 } }),
                ]),
              ]),
            ),
            text("↔", { width: hug, height: hug, style: { fontSize: 36, bold: true, color: C.green } }),
            panel(
              { width: fixed(600), height: fixed(110), fill: C.white, padding: { x: 24, y: 18 }, borderRadius: 12 },
              row({ width: fill, height: fill, gap: 18, align: "center" }, [
                shape({ geometry: "ellipse", width: fixed(52), height: fixed(52), fill: C.green }),
                column({ width: fill, height: hug, gap: 6 }, [
                  text("State（家庭状态）", { width: fill, height: hug, style: { fontSize: 28, bold: true, color: C.ink } }),
                  text("设备状态 / 传感器数据 / 场景状态 / 网络状态\n实时维护，支撑决策与回复", { width: fill, height: hug, style: { fontSize: 17, color: C.ink2 } }),
                ]),
              ]),
            ),
          ]),
        ]),
      ]),
    ),
    row({ width: fill, height: hug, justify: "between", align: "center" }, [
      row({ width: hug, height: hug, gap: 30, align: "center" }, [
        legendItem("交互流", C.blue),
        legendItem("主链路流", "#D66A00"),
        legendItem("能力调用与数据流", C.green),
      ]),
      panel(
        { width: fixed(760), height: fixed(58), fill: "#F3F8FF", padding: { x: 22, y: 12 }, borderRadius: 10 },
        text("核心价值：真正理解意图、规划任务、调用工具、更新状态、生成回复。", {
          width: fill,
          height: hug,
          align: "center",
          style: { fontSize: 20, bold: true, color: C.ink },
        }),
      ),
      text("14/20", { width: fixed(78), height: hug, style: { fontSize: 18, bold: true, color: C.quiet } }),
    ]),
  ]),
);

// 15. Agent architecture
addSlide(
  "agent",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 78, y: 66 }, justify: "between", gap: 30 }, [
    title("核心方案一：混合意图路由与本地模型补识别", "系统采用规则优先的低延迟路径；规则未命中时由本地 Qwen 识别意图，识别结果仍进入规划和工具执行。"),
    grid({ width: fill, height: hug, columns: [fr(1), auto, fr(1), auto, fr(1), auto, fr(1), auto, fr(1)], columnGap: 14, alignItems: "center" }, [
      step("规则", "高频家庭任务低延迟命中", C.teal),
      text("→", { width: hug, height: fixed(132), style: { fontSize: 42, color: C.quiet2, bold: true } }),
      step("Qwen", "规则未命中时补识别意图", C.blue),
      text("→", { width: hug, height: fixed(132), style: { fontSize: 42, color: C.quiet2, bold: true } }),
      step("Planner", "意图转可执行 DAG", C.amber),
      text("→", { width: hug, height: fixed(132), style: { fontSize: 42, color: C.quiet2, bold: true } }),
      step("Tools", "sensor / device / network 等", C.green),
      text("→", { width: hug, height: fixed(132), style: { fontSize: 42, color: C.quiet2, bold: true } }),
      step("回复", "由工具结果汇总生成", C.coral),
    ]),
    panel(
      { width: fill, height: hug, padding: { x: 34, y: 26 }, fill: C.mist, borderRadius: 12 },
      text("实现路径：LocalRouter → TaskPlanner → PlanExecutor → ToolRegistry → Pipeline._reply。回复依据 tool_results 汇总生成；没有可执行工具或可信知识命中时，才进入本地模型生成式兜底。", {
        width: fill,
        height: hug,
        style: { fontSize: 27, bold: true, color: C.ink },
      }),
    ),
    footer(15),
  ]),
);

// 16. Tools
addSlide(
  "tools",
  C.cloud,
  column({ width: fill, height: fill, padding: { x: 82, y: 64 }, justify: "between", gap: 26 }, [
    title("核心方案二：工具注册表与白名单执行", "设备、网络、提醒、知识和安全能力统一注册为工具函数，规划器只能调用明确声明的本地工具。"),
    grid({ width: fill, height: fill, columns: [fr(1), fr(1), fr(1)], rows: [fr(1), fr(1)], columnGap: 24, rowGap: 24 }, [
      plainPanel("tool-device", column({ width: fill, height: fill, gap: 12 }, [
        text("设备与场景", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.teal } }),
        text("device.control\nscene.apply\ndevice.query", { width: fill, height: hug, style: type.body }),
      ])),
      plainPanel("tool-network", column({ width: fill, height: fill, gap: 12 }, [
        text("网络诊断", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.blue } }),
        text("network.diagnose\nnetwork.apply_qos\nMesh / RSSI / 带宽占用", { width: fill, height: hug, style: type.body }),
      ])),
      plainPanel("tool-reminder", column({ width: fill, height: fill, gap: 12 }, [
        text("提醒管理", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.amber } }),
        text("reminder.create\nreminder.query\nreminder.complete / cancel", { width: fill, height: hug, style: type.body }),
      ])),
      plainPanel("tool-profile", column({ width: fill, height: fill, gap: 12 }, [
        text("家庭画像", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.green } }),
        text("home_profile.query\nprofile.remember\nprofile.query", { width: fill, height: hug, style: type.body }),
      ])),
      plainPanel("tool-knowledge", column({ width: fill, height: fill, gap: 12 }, [
        text("知识检索", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.violet } }),
        text("knowledge.search\nSQLite 本地知识库\n无命中不编造", { width: fill, height: hug, style: type.body }),
      ])),
      plainPanel("tool-safety", column({ width: fill, height: fill, gap: 12 }, [
        text("安全确认", { width: fill, height: hug, style: { fontSize: 30, bold: true, color: C.coral } }),
        text("safety.check\n门锁/摄像头/告警\npending_confirmations", { width: fill, height: hug, style: type.body }),
      ])),
    ]),
    footer(16),
  ]),
);

// 17. Memory
addSlide(
  "memory",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 86, y: 68 }, justify: "between", gap: 32 }, [
    title("核心方案三：状态记忆与本地知识约束", "短期状态负责多轮承接，长期画像负责家庭成员偏好，本地知识库负责可追溯的家庭规则和解释来源。"),
    row({ width: fill, height: fill, gap: 42, align: "stretch" }, [
      column({ width: fill, height: fill, gap: 22, justify: "center" }, [
        text("短期状态", { width: fill, height: hug, style: { fontSize: 35, bold: true, color: C.teal } }),
        bullet("保存最近对话、上一轮意图、房间、成员、待确认动作。"),
        bullet("支持“先保证爷爷那边”这类多轮上下文。", C.blue),
        bullet("LLM 兜底回答会读取最近历史，避免答非所问。", C.green),
      ]),
      plainPanel("memory-example", column({ width: fill, height: fill, gap: 22, justify: "center" }, [
        text("长期画像示例", { width: fill, height: hug, style: { fontSize: 35, bold: true, color: C.amber } }),
        text("爷爷｜性格：节俭\n饮食：不吃辣，喜欢清淡\n爱好：散步\n\n奶奶｜爱好：看电影\n饮食：喜欢番茄炒蛋", {
          width: fill,
          height: hug,
          style: { fontSize: 30, color: C.ink2 },
        }),
        text("实现：SQLite family_profiles 表，本地持久化，前端画像区域自动刷新。", {
          width: fill,
          height: hug,
          style: { fontSize: 20, color: C.quiet },
        }),
      ]), "#FFF8E8"),
    ]),
    footer(17),
  ]),
);

// 18. Edge trust
addSlide(
  "trust",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 86, y: 68 }, justify: "between", gap: 30 }, [
    title("端侧可信：隐私、安全、成本和可解释性一起成立", "系统以本地模型、本地数据库和本地工具执行为基础，在低资源环境中完成可追踪的家庭智能体流程。"),
    row({ width: fill, height: fill, gap: 34, align: "stretch" }, [
      column({ width: fill, height: fill, gap: 18, justify: "center" }, [
        bullet("本地量化模型：Qwen2.5-1.5B-Instruct Q4_K_M GGUF。", C.blue),
        bullet("本地数据：SQLite 保存知识库和家庭画像。", C.green),
        bullet("本地工具：设备、网络、提醒、传感器均由白名单工具执行。", C.teal),
        bullet("安全门：高风险动作必须二次确认。", C.coral),
        bullet("高效响应：规则毫秒级路径，本地模型仅在不确定时参与。", C.violet),
        bullet("可解释：每轮返回 intent、plan、tool_results、metrics。", C.amber),
      ]),
      grid({ width: fill, height: hug, columns: [fr(1), fr(1)], rows: [auto, auto], columnGap: 22, rowGap: 22 }, [
        plainPanel("metric-rule", column({ width: fill, height: hug, gap: 8 }, [
          text("毫秒级", { width: fill, height: hug, style: { fontSize: 50, bold: true, color: C.teal } }),
          text("规则路径", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2, bold: true } }),
        ]), "#EEF8F5"),
        plainPanel("metric-model", column({ width: fill, height: hug, gap: 8 }, [
          text("可追踪", { width: fill, height: hug, style: { fontSize: 50, bold: true, color: C.blue } }),
          text("模型调用指标", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2, bold: true } }),
        ]), "#EEF4FF"),
        plainPanel("metric-safe", column({ width: fill, height: hug, gap: 8 }, [
          text("本地化", { width: fill, height: hug, style: { fontSize: 50, bold: true, color: C.green } }),
          text("隐私数据不出端", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2, bold: true } }),
        ]), "#EFF8F2"),
        plainPanel("metric-demo", column({ width: fill, height: hug, gap: 8 }, [
          text("可演示", { width: fill, height: hug, style: { fontSize: 50, bold: true, color: C.amber } }),
          text("四条主线闭环", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2, bold: true } }),
        ]), "#FFF8E8"),
      ]),
    ]),
    footer(18),
  ]),
);

// 19. Summary
addSlide(
  "summary",
  C.cloud,
  column({ width: fill, height: fill, padding: { x: 88, y: 68 }, justify: "between", gap: 32 }, [
    title("作品总结：一个可运行的端侧家庭智能体", "把赛题要求的理解、规划、工具调用、多轮状态和高效推理落到可演示系统中。"),
    row({ width: fill, height: fill, gap: 48, align: "stretch" }, [
      column({ width: fill, height: fill, justify: "center", gap: 22 }, [
        text("不是单纯聊天，而是把家庭任务真正执行起来。", {
          width: wrap(760),
          height: hug,
          style: { fontSize: 52, bold: true, color: C.ink },
        }),
        text("用户一句话进入系统后，会经历意图识别、DAG 规划、白名单工具执行、状态更新和结果解释；每一步都能在 Demo 界面里被看到。", {
          width: wrap(780),
          height: hug,
          style: { fontSize: 27, color: C.ink2 },
        }),
        row({ width: fill, height: hug, gap: 12 }, [
          chip("场景理解", C.teal),
          chip("任务规划", C.blue),
          chip("工具调用", C.green),
          chip("状态保持", C.amber),
          chip("端侧推理", C.coral),
        ]),
      ]),
      grid({ width: fixed(820), height: fill, columns: [fr(1), fr(1)], rows: [fr(1), fr(1)], columnGap: 22, rowGap: 22 }, [
        plainPanel("summary-scene", column({ width: fill, height: fill, gap: 12, justify: "center" }, [
          text("场景落地", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.teal } }),
          text("睡前联动、老人关怀、网络 QoS、主动巡检都能从快捷场景直接触发。", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2 } }),
        ]), "#EEF8F5"),
        plainPanel("summary-agent", column({ width: fill, height: fill, gap: 12, justify: "center" }, [
          text("智能体闭环", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.blue } }),
          text("规则未命中时由本地模型补识别，随后仍交给 Planner 和工具链执行。", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2 } }),
        ]), "#EEF4FF"),
        plainPanel("summary-memory", column({ width: fill, height: fill, gap: 12, justify: "center" }, [
          text("家庭记忆", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.amber } }),
          text("长期画像保存成员性格、爱好和饮食偏好，让后续建议更像家庭中枢。", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2 } }),
        ]), "#FFF8E8"),
        plainPanel("summary-trust", column({ width: fill, height: fill, gap: 12, justify: "center" }, [
          text("端侧可信", { width: fill, height: hug, style: { fontSize: 34, bold: true, color: C.green } }),
          text("本地模型、本地 SQLite、本地工具日志和性能指标共同支撑隐私与可解释性。", { width: fill, height: hug, style: { fontSize: 22, color: C.ink2 } }),
        ]), "#EFF8F2"),
      ]),
    ]),
    panel(
      { width: fill, height: hug, padding: { x: 34, y: 26 }, fill: C.darkBg, borderRadius: 12 },
      text("最终定位：面向三代同堂家庭的本地任务中枢，用可控工具执行承接自然语言交互。", {
        width: fill,
        height: hug,
        style: { fontSize: 32, bold: true, color: C.white },
      }),
    ),
    footer(19),
  ]),
);

// 20. Thanks
addSlide(
  "thanks",
  C.paper,
  column({ width: fill, height: fill, padding: { x: 92, y: 76 }, justify: "between", gap: 36 }, [
    row({ width: fill, height: hug, justify: "between", align: "center" }, [
      text("兴享智家 · 慧家中枢", { width: hug, height: hug, style: { fontSize: 26, bold: true, color: C.teal } }),
      text("西安电子科技大学广州研究院", { width: hug, height: hug, style: { fontSize: 22, color: C.quiet } }),
    ]),
    column({ width: fill, height: hug, gap: 28, align: "center" }, [
      text("谢谢", { width: hug, height: hug, style: { fontSize: 132, bold: true, color: C.ink } }),
      rule({ width: fixed(360), stroke: C.amber, weight: 6 }),
      text("欢迎交流与提问", { width: hug, height: hug, style: { fontSize: 46, bold: true, color: C.teal } }),
      text("面向真实家庭任务的端侧智能体，让关怀、设备、网络和安全在本地形成闭环", {
        width: wrap(1200),
        height: hug,
        align: "center",
        style: { fontSize: 27, color: C.ink2 },
      }),
    ]),
    row({ width: fill, height: hug, justify: "center", gap: 12 }, [
      chip("老人关怀", C.teal),
      chip("睡前联动", C.amber),
      chip("网络 QoS", C.blue),
      chip("主动巡检", C.green),
      chip("本地记忆", C.coral),
    ]),
  ]),
);

await mkdir(OUT_DIR, { recursive: true });
await mkdir(PREVIEW_DIR, { recursive: true });

const pptxBlob = await PresentationFile.exportPptx(presentation);
const pptxPath = path.join(OUT_DIR, PPTX_NAME);
await pptxBlob.save(pptxPath);

for (let i = 0; i < presentation.slides.count; i += 1) {
  const slide = presentation.slides.getItem(i);
  const pngBlob = await slide.export({ format: "png" });
  const buffer = Buffer.from(await pngBlob.arrayBuffer());
  await writeFile(path.join(PREVIEW_DIR, `slide-${String(i + 1).padStart(2, "0")}.png`), buffer);
}

console.log(JSON.stringify({ slides: presentation.slides.count, pptx: pptxPath, previews: PREVIEW_DIR }, null, 2));
