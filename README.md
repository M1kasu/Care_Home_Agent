# 兴享智家·慧家中枢

面向三代同堂家庭的端侧家庭智能体 Demo。系统通过规则优先、本地 Qwen 小模型兜底、SQLite 长期记忆和白名单工具调用，把自然语言转成可执行的家庭任务闭环。

## 核心能力

- 场景理解与任务规划：睡前模式、离家模式、观影模式、儿童学习模式等。
- 工具调用与资源整合：设备控制、网络诊断、QoS、提醒、传感器、能耗、知识库、长期画像。
- 多轮状态保持：支持网络诊断后的 QoS 跟进、敏感动作二次确认、普通生活问答追问。
- 端侧运行：本地 GGUF 模型、本地 SQLite、本地工具执行，核心流程不依赖云 API。

## 项目结构

```text
main.py                         比赛要求的 run 入口
smart_home_agent/               Agent 核心代码
  core/                         Router / Planner / Executor
  tools/                        ToolRegistry 与家庭工具
  memory/                       SQLite 知识库、长期画像、会话记忆
  providers/                    本地 LLM 提供方
demo/app.py                     Gradio 演示界面
tests/test_scenarios.py         场景烟雾测试
zhijia/docs/                    需求、接口、实现方案文档
pptx_work/                      复赛 PPT 生成脚本与最终 PPT
qa.md                           答辩问答库
复赛技术说明文档.md              技术说明文档
```

## 安装

建议使用 Python 3.10+。

```powershell
python -m pip install -e ".[demo]"
python -m pip install "llama-cpp-python==0.3.19" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu --prefer-binary
```

## 本地模型

GitHub 仓库不包含 `smart_home_agent/data/qwen2.5-1.5b-instruct-q4_k_m.gguf`，因为模型文件约 940MB。运行本地模型前请下载：

```powershell
python scripts\download_model.py
```

也可以手动下载 Qwen2.5-1.5B-Instruct Q4_K_M GGUF，并放到：

```text
smart_home_agent/data/qwen2.5-1.5b-instruct-q4_k_m.gguf
```

## 运行 Demo

```powershell
python demo\app.py
```

浏览器打开：

```text
http://127.0.0.1:7860/
```

## 命令行调用

```powershell
python main.py "爸妈准备睡了，帮我切到睡前模式，顺便检查一下门锁。"
```

也可以在 Python 中调用：

```python
from main import run

result = run("爷爷房间视频有点卡，帮我看看。")
print(result["reply"])
```

## 测试

```powershell
$env:PYTHONIOENCODING="utf-8"
python tests\test_scenarios.py
```

## 说明

- 当前设备、网络和传感器为本地模拟数据，方便比赛现场稳定演示。
- `home_tools.py` 的模拟工具可以替换成 Matter、MQTT、Home Assistant、路由器 API 等真实接口。
- 长期家庭画像和本地知识库保存在 SQLite 中，运行时数据库文件不会提交到 GitHub。
