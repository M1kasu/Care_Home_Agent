param(
    [string]$SourcePptx = (Join-Path (Split-Path $PSScriptRoot -Parent) 'output\兴享智家_慧家中枢_复赛产品介绍_评分维度强化版.pptx'),
    [string]$OutputPptx = (Join-Path (Split-Path $PSScriptRoot -Parent) 'output\兴享智家_慧家中枢_复赛产品介绍_评分维度强化版_含演讲备注.pptx')
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$notes = @{}
$notes[1] = @'
【预计 0:50】
各位老师好，我们的作品叫“兴享智家·慧家中枢”。一句话介绍，它是面向三代同堂家庭的本地任务中枢。
它的核心目标，是把家庭里的老人关怀、睡前联动、网络 QoS、主动巡检和安全确认这些真实任务，用自然语言统一起来。用户说一句话，系统在本地完成理解、规划、调用工具和生成回复。
这套系统强调端侧落地：本地 Qwen、规则路由、SQLite 记忆和工具闭环都在本地运行，后面我会从产品价值、赛题能力、评分维度、Demo 功能和技术架构几个层面展开。
'@
$notes[2] = @'
【预计 1:10】
这一页先说明我们为什么选择家庭场景。家庭智能化看起来设备很多，但真实使用时有几个核心问题。
第一是设备入口割裂，灯、空调、门锁、电视、路由器分散在不同 App 或面板里。第二是网络问题很难定位，老人房视频卡顿，普通家庭成员很难判断是 Mesh 信号、带宽占用还是设备问题。
第三是关怀任务缺少上下文，提醒工具只知道“几点提醒”，不知道提醒对象是谁、有没有回应、后续是否要复提醒。第四是隐私问题，家庭作息、健康提醒、摄像头和网络日志都不适合默认上传云端。
所以我们的切入点是做一个能理解家庭状态、能调工具、能记住家庭成员偏好的本地家庭中枢。
'@
$notes[3] = @'
【预计 1:20】
这一页是产品定位。我们明确选择的是“面向三代同堂家庭的本地任务中枢”。
系统可以部署在家庭网关、边缘盒子或类似端侧设备上，把家庭成员、房间、设备、网络、提醒和知识组织成一个可执行的状态空间。
用户侧只需要说一句自然语言，比如“爷爷房间视频有点卡，帮我看看”，系统就会完成意图理解、任务规划、工具调用、状态更新和解释回复。
产品价值集中在四条主线：老人关怀、睡前联动、网络 QoS、主动巡检。儿童学习、能耗查询和知识问答作为辅助能力存在，但不是主叙事。这样更符合赛题中“场景化智能体”的要求，也更容易在现场稳定演示。
'@
$notes[4] = @'
【预计 1:40】
这一页直接对齐赛题能力。左边是题目要求的四项核心能力，右边是我们的创新方向落地。
第一，场景理解与任务规划。我们通过 Router 和本地 Qwen 识别家庭自然语言，再由 TaskPlanner 生成 DAG 任务计划。第二，工具调用与资源整合。所有设备、网络、提醒、知识、画像和安全能力都注册在 ToolRegistry 中，由 PlanExecutor 按计划调用。
第三，多轮对话与状态保持。系统维护 Session State，并用 SQLite 保存长期家庭画像，比如爷爷不吃辣、奶奶喜欢番茄炒蛋。第四，高效推理与实时响应。高频任务走规则毫秒级路径，只有规则不确定时才调用量化本地模型。
创新点包括轻量模型意图理解、端侧 Agent 架构、多源场景感知、模型量化、本地知识库和低资源持续适应。核心就是在家庭场景中完成从理解到执行的智能体闭环。
'@
$notes[5] = @'
【预计 1:20】
这一页对齐评分标准。比赛总分 100 分，创新、价值、成本、演示和文档各 20 分，我们希望每个维度都有可展示证据。
创新方面，我们从通用问答升级成家庭端侧任务中枢，结合轻量模型、工具规划、长期画像和本地知识。价值方面，我们瞄准三代同堂家庭的真实问题：老人关怀、睡前联动、网络诊断和主动巡检。
成本方面，系统采用规则优先降低推理开销，本地量化 Qwen 只在不确定时参与，数据保存在 SQLite。演示方面，我们有可运行 Web Demo，能看到快捷场景、意图、DAG、工具日志、设备状态和传感器状态。
文档方面，方案文档、接口文档、技术说明、PPT 和 Demo 口径一致，可以追溯到代码模块。也就是说，我们不是只讲想法，而是把评分维度都落到了可看的页面和可跑的工程上。
'@
$notes[6] = @'
【预计 1:30】
这一页展示四类核心家庭任务闭环。
第一是老人关怀，包括吃药提醒、完成或取消、未响应复提醒，以及老人房状态查询。第二是睡前联动，系统可以关闭电视、调暗灯光、调整空调睡眠模式并检查门锁。
第三是网络 QoS，当老人房视频卡顿时，系统会诊断网络状态，并可以对老人房视频开启优先策略。第四是主动巡检，系统读取传感器状态，发现低温、久未活动或其他异常时给出提示，并对敏感动作做安全确认。
这四类任务都不是单独的固定回答，而是对应一组工具调用。自然语言进入系统后，会被转成计划，再调用 reminder、sensor、device、network、scene 和 safety 等工具，最后根据工具结果生成回复。
'@
$notes[7] = @'
【预计 1:10】
这页用一个晚上的时间线来说明用户体验。
晚上 19:30，孩子进入学习模式，灯光切到护眼，系统安排休息提醒。20:30，老人房视频卡顿，系统进行网络诊断并开启 QoS。21:00，爷爷吃药提醒，如果未回应，系统会在 10 分钟后再次提醒。
22:30，用户触发睡前模式，系统联动设备、检查门锁，并确认老人房状态。夜间，主动巡检会继续关注低温、久未活动或安全异常。
这个时间线体现的是持续服务能力：同一套 Agent 跨越成员、房间、设备、网络、提醒和知识，减少家庭成员在多个 App 之间来回切换。
'@
$notes[8] = @'
【预计 1:10】
这一页是 Demo 界面总览。我们刻意把智能体运行过程可视化，而不是只展示一个聊天框。
左侧是对话窗口和用户输入区，用户可以自然语言提问，也可以通过快捷场景按钮触发主线任务。右侧是运行策略、意图识别、本地模型状态、长期家庭画像、任务规划 DAG、工具调用日志、设备状态面板和传感器面板。
这样设计的目的，是让评审能看到每一轮请求背后的过程：意图来自规则还是本地模型，置信度是多少，Planner 生成了哪些步骤，Executor 调用了哪些工具，工具返回了什么结果，状态有没有更新。
所以这个界面本身就是作品完成度的证据。
'@
$notes[9] = @'
【预计 1:20】
这一页介绍快捷场景和运行策略。快捷场景不是静态按钮，而是把真实自然语言模板送入同一个 main.run 入口。
比如“网络诊断”对应“爷爷房间视频有点卡，帮我看看”；“吃药提醒”对应“提醒爷爷晚上九点吃降压药，如果十分钟没回应就再提醒一次”。这样现场演示时可以稳定触发主线场景，同时仍然走完整 Agent 流程。
右侧是运行策略。自动闭环是推荐模式：规则优先，规则不确定时调用本地 Qwen 补识别，识别后继续走工具。规则仅调试用于展示低延迟路径，也证明没有模型时核心场景仍能运行。强制模型识别用于现场稳定展示 local_llm 参与，但最终回复仍然来自工具结果。
这能清楚说明：我们不是把模型当万能聊天接口，而是把模型放在可控的 Agent 流程中。
'@
$notes[10] = @'
【预计 1:20】
这一页是长期记忆和家庭画像。我们之前发现单纯靠短期上下文，会出现用户追问“什么步骤”时系统不知道上一轮在说什么的问题。
因此现在系统同时有短期会话状态和长期家庭画像。比如用户说“记住奶奶喜欢吃番茄炒蛋”，系统会通过 profile.remember 提取成员和偏好，写入本地 SQLite。之后用户问“中午吃什么好”，系统就能结合奶奶的偏好给出建议。
右侧的家庭画像面板会实时刷新，包括奶奶、爷爷、孩子、爸爸等成员的爱好、性格和饮食偏好。这个功能体现了多轮状态保持和低资源持续适应：它不需要重新训练模型，而是通过本地结构化记忆，让系统越来越贴近这个家庭。
'@
$notes[11] = @'
【预计 1:20】
这一页展示意图识别和任务规划 DAG。
每次用户输入后，右侧都会显示意图名称、来源、置信度和槽位。例如“爷爷房间视频有点卡，帮我看看”，可能识别为 network_qos 或 network_diagnosis，槽位里包含 room 是老人房，member 是爷爷。
如果规则稳定命中，就直接进入规划；如果规则不确定，本地 Qwen 输出结构化 JSON，包含 intent、confidence 和 slots。只要识别到可执行家庭任务，后续仍进入 Planner 和工具链。
右侧 DAG 说明系统不是直接吐固定话术，而是先拆任务再执行。比如先查家庭画像，再诊断网络，再开启 QoS，最后基于工具结果生成回复。这个 DAG 也是安全确认和依赖管理的基础。
'@
$notes[12] = @'
【预计 1:20】
这一页展示工具日志、设备状态和传感器面板。
左侧工具日志记录每一步调用了哪个工具、结果是什么、耗时多少。比如 home_profile.query 读取爷爷和老人房画像，sensor.query 读取老人房温湿度和活动状态，device.query 读取设备状态，network.apply_qos 开启老人房视频优先。
右侧设备状态面板展示客厅灯、主卧空调、老人房空调、门锁等状态；传感器面板展示老人房、儿童房、客厅的温度、湿度、活动和噪声。
这页的价值在于证明系统有“执行痕迹”。评审如果追问某个动作为什么发生，我们可以从工具日志、设备表和传感器表里解释，而不是只看一段自然语言回复。
'@
$notes[13] = @'
【预计 1:10】
这一页是接口契约。比赛要求系统有明确入口，我们围绕 main.run 设计了统一接口，命令行、Web Demo 和测试脚本都复用这个入口。
输入包括 user_input、state 和 config。user_input 是用户自然语言，state 是会话和家庭状态，config 包括模型策略、确认策略、安全策略和调试配置。
输出不是单独一句 reply，而是一组结构化结果：reply、intent、plan、tool_results、state、metrics 和 safety。这样前端能展示意图识别、任务 DAG、工具日志和性能指标；测试脚本也能直接断言工具调用和状态更新。
这个接口保证了演示界面和后端智能体不是两套东西，而是同一个核心入口。
'@
$notes[14] = @'
【预计 1:40】
这一页是整体项目框架图，也是技术架构的总览。
最上层是交互层，用户可以通过自然语言或快捷场景进入 Gradio Demo，最后统一调用 main.run。中间是 Agent 主链路：Pipeline 编排整体流程，Router 做规则优先的意图路由，本地 Qwen 负责兜底识别，Planner 生成计划，Executor 按依赖执行，ToolRegistry 统一管理工具，Reply Builder 汇总结果生成回复。
底层是本地能力层，包括传感器、设备控制、场景联动、网络诊断、提醒管理、长期画像、知识库和安全确认。这些能力与 SQLite 和 State 形成数据闭环。
这张图想表达的是：我们的前端不是假界面，后端也不是单个聊天接口，而是一套端侧 Agent 执行闭环。交互流、主链路流和能力数据流都是可以追踪的。
'@
$notes[15] = @'
【预计 1:20】
这一页进入核心方案一：混合意图路由与本地模型补识别。
我们没有让所有请求都进模型，因为端侧算力有限，且家庭高频任务往往可以用规则快速识别。规则路径用于睡前模式、提醒、设备查询、传感器查询等高频任务，延迟低、稳定性强。
当规则没有稳定命中时，再调用本地 Qwen 做意图补识别。模型输出的不是自由文本，而是结构化意图和槽位。之后仍然进入 Planner 和工具执行。
最后的回复由工具结果汇总生成。只有当没有可执行工具或没有可信知识命中时，才进入本地模型直接回答兜底。这样既保留了模型的泛化能力，也保证了家庭任务的可控性和可解释性。
'@
$notes[16] = @'
【预计 1:20】
这一页是核心方案二：工具注册表与白名单执行。
系统里的能力不是散落在代码里的 if else，而是统一注册为工具函数。设备与场景包括 device.control、scene.apply、device.query；网络诊断包括 network.diagnose 和 network.apply_qos；提醒管理包括 reminder.create、reminder.query、reminder.complete 和 reminder.cancel。
家庭画像有 profile.remember 和 profile.query；知识检索有 knowledge.search；安全确认有 safety.check。
规划器只能调用这些明确声明的本地工具。这样做有两个好处：第一，工具边界清晰，方便扩展到真实设备；第二，敏感动作可以被统一拦截，比如门锁解锁必须经过安全确认。
'@
$notes[17] = @'
【预计 1:10】
这一页是核心方案三：状态记忆与本地知识约束。
短期状态负责多轮承接，包括最近对话、上一轮意图、房间、成员和待确认动作。比如用户上一轮说“看看老人房现在怎么样”，下一轮说“先保证爷爷那边”，系统能继承老人房和爷爷这个上下文。
长期画像负责家庭成员偏好，比如爷爷节俭、不吃辣、喜欢清淡，奶奶喜欢看电影、喜欢番茄炒蛋。这些信息保存在 SQLite 中，不依赖外部服务。
本地知识库用于家庭规则和解释来源。知识检索设置了可信阈值和无答案回退，避免本地知识库没命中时硬编答案。这样系统在能回答时给来源，在不能确定时保持保守。
'@
$notes[18] = @'
【预计 1:20】
这一页讲端侧可信，也对应评分里的成本和可解释性。
本地模型使用 Qwen2.5-1.5B-Instruct Q4_K_M GGUF，这是适合低资源设备的量化模型。高频任务优先走规则路径，模型只在不确定时参与，降低推理开销。
本地数据使用 SQLite 保存知识库和家庭画像，隐私数据不出端。本地工具包括设备、网络、提醒和传感器，全部通过白名单执行。高风险动作，例如门锁解锁，会触发二次确认。
每轮请求都会返回 intent、plan、tool_results 和 metrics，所以我们可以解释“为什么这么做”“调用了什么工具”“模型有没有参与”“耗时是多少”。这对现场答辩非常关键。
'@
$notes[19] = @'
【预计 1:00】
这一页做总结。我们的核心结论是：兴享智家不是单纯聊天，而是把家庭任务真正执行起来。
从用户一句话进入系统开始，它会经历场景理解、任务规划、工具调用、状态保持和端侧推理。场景落地包括睡前联动、老人关怀、网络 QoS 和主动巡检；智能体闭环包括规则补识别、本地模型、Planner 和工具链；家庭记忆包括长期画像和本地知识；端侧可信包括本地模型、SQLite、工具日志和性能指标。
最终定位就是：面向三代同堂家庭的本地任务中枢，用可控工具执行承接自然语言交互。
'@
$notes[20] = @'
【预计 0:20】
我的介绍到这里结束。
最后再用一句话收束：兴享智家·慧家中枢面向真实家庭任务，让关怀、设备、网络和安全在本地形成闭环。
谢谢各位老师，欢迎交流与提问。
'@

function Escape-XmlText {
    param([string]$Text)
    return [System.Security.SecurityElement]::Escape($Text)
}

function New-ParagraphXml {
    param([string]$Line)
    $escaped = Escape-XmlText $Line
    return "<a:p><a:r><a:rPr lang=`"zh-CN`" sz=`"1400`"/><a:t>$escaped</a:t></a:r><a:endParaRPr lang=`"zh-CN`" sz=`"1400`"/></a:p>"
}

function New-NotesSlideXml {
    param(
        [int]$SlideNumber,
        [string]$NoteText
    )
    $paragraphs = ($NoteText -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 } | ForEach-Object { New-ParagraphXml $_ }) -join ''
    return "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?>" +
        "<p:notes xmlns:a=`"http://schemas.openxmlformats.org/drawingml/2006/main`" xmlns:r=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships`" xmlns:p=`"http://schemas.openxmlformats.org/presentationml/2006/main`">" +
        "<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id=`"1`" name=`"`"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x=`"0`" y=`"0`"/><a:ext cx=`"0`" cy=`"0`"/><a:chOff x=`"0`" y=`"0`"/><a:chExt cx=`"0`" cy=`"0`"/></a:xfrm></p:grpSpPr>" +
        "<p:sp><p:nvSpPr><p:cNvPr id=`"2`" name=`"Slide Image Placeholder 1`"/><p:cNvSpPr><a:spLocks noGrp=`"1`" noRot=`"1`" noChangeAspect=`"1`"/></p:cNvSpPr><p:nvPr><p:ph type=`"sldImg`"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>" +
        "<p:sp><p:nvSpPr><p:cNvPr id=`"3`" name=`"Notes Placeholder 2`"/><p:cNvSpPr><a:spLocks noGrp=`"1`"/></p:cNvSpPr><p:nvPr><p:ph type=`"body`" idx=`"1`"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>$paragraphs</p:txBody></p:sp>" +
        "<p:sp><p:nvSpPr><p:cNvPr id=`"4`" name=`"Slide Number Placeholder 3`"/><p:cNvSpPr><a:spLocks noGrp=`"1`"/></p:cNvSpPr><p:nvPr><p:ph type=`"sldNum`" idx=`"5`"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr/></a:p></p:txBody></p:sp>" +
        "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>"
}

$source = Resolve-Path -LiteralPath $SourcePptx
$outputDir = Split-Path -Parent $OutputPptx
if (-not (Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}
Copy-Item -LiteralPath $source -Destination $OutputPptx -Force

$zip = [System.IO.Compression.ZipFile]::Open($OutputPptx, [System.IO.Compression.ZipArchiveMode]::Update)
try {
    foreach ($slideNumber in 1..20) {
        $entryPath = "ppt/notesSlides/notesSlide$slideNumber.xml"
        $existing = $zip.GetEntry($entryPath)
        if ($existing) {
            $existing.Delete()
        }
        $entry = $zip.CreateEntry($entryPath, [System.IO.Compression.CompressionLevel]::Optimal)
        $stream = $entry.Open()
        $writer = [System.IO.StreamWriter]::new($stream, [System.Text.UTF8Encoding]::new($false))
        $writer.Write((New-NotesSlideXml -SlideNumber $slideNumber -NoteText $notes[$slideNumber]))
        $writer.Dispose()
        $stream.Dispose()
    }
}
finally {
    $zip.Dispose()
}

Write-Host "Wrote speaker notes to $OutputPptx"

