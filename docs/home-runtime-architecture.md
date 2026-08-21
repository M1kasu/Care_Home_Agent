# 内嵌 Home Runtime 架构

## 目标与阶段状态

当前实现完成前三个阶段：

1. 在 Home Agent 进程内建立轻量 Runtime 内核，不启动单独的 Home Assistant。
2. 把设备、场景、网络、提醒、传感器和能耗能力迁入 `SimulatorIntegration`。
3. 用实体状态事件驱动照护告警，并用状态化 Scheduler 承载设备定时动作和提醒重试。

本阶段没有复制 Home Assistant 源码。这样可以先稳定项目的领域边界；后续若引入 HA 代码，应以一个或多个 Integration 的形式接入，而不是让 Agent 直接依赖 HA 内部对象。

## 单进程调用链

```text
Gradio / main.run
        |
        v
SmartHomeAgent Pipeline
  Router -> Planner -> Executor -> Agent ToolRegistry
                                   |
                                   v
                         HomeRuntimeFacade
                                   |
          +------------------------+-------------------------+
          |                        |                         |
    ServiceRegistry          StateMachine               Scheduler
          |                        |                         |
          v                        v                         v
 SimulatorIntegration         EventBus             延迟 Service 调用
                                   |
                                   v
                            CarePolicyEngine
```

所有组件都在同一 Python 进程、同一份家庭 State 上工作。Agent 面向自然语言任务；Runtime 面向确定性的家庭服务、实体状态、事件和调度。

## 模块职责

| 模块 | 职责 | 允许依赖 |
|---|---|---|
| `pipeline.py` | 组合 Agent 与 Runtime，控制一次请求生命周期 | Agent core、Runtime 公共接口、Integration 工厂 |
| `tools/home_tools.py` | Agent 白名单工具到 Runtime Service 的薄适配 | Runtime Facade、记忆组件 |
| `home_runtime/runtime.py` | Runtime 组合根和窄门面 | Runtime 核心模块 |
| `event_bus.py` | 同步发布/订阅和事件日志 | Runtime model |
| `state_machine.py` | 统一实体状态并发出 `state_changed` | Event Bus |
| `service_registry.py` | 注册/调用确定性服务，隔离异常并记录调用 | 无业务模块 |
| `scheduler.py` | 保存延迟任务并调用已注册 Service | Service Registry |
| `registries.py` | 管理实体、设备和区域元数据 | Runtime model |
| `care_policy.py` | 监听传感器事件，维护照护告警生命周期 | Event Bus、家庭状态 |
| `integrations/simulator.py` | 当前比赛业务实现和模拟数据 | Runtime 注册表、状态机、服务上下文 |

## 耦合度与扩展边界

- Runtime 核心不依赖 Router、Planner、LLM、Gradio、SQLite 画像或具体设备，属于低业务耦合。
- Agent ToolRegistry 只依赖 `HomeRuntimeFacade.call_service`，不再直接调用模拟设备函数，耦合由“实现级”降为“服务契约级”。
- `SimulatorIntegration` 内部仍聚合了比赛阶段的多个业务域，属于中等内聚、可接受的阶段性耦合；真实接入时可按 `matter`、`mqtt`、`network`、`care` 拆为多个 Integration。
- `pipeline.py` 是明确的组合根，默认装配 `SimulatorIntegration`。构造 `SmartHomeAgent` 时可传入其他 Integration 工厂，不需要修改 Planner 和 UI。
- 照护策略只订阅实体事件，不依赖传感器采集协议；传感器从模拟器换成 Matter/MQTT 后，策略可以保持不变。

## 后续融合 Home Assistant 的方式

不运行第二套 HA 服务。建议从 HA 中选择真正需要的能力，包装为本项目的 Integration：

- 复用实体与设备抽象时，转换成当前 `EntityRecord`、`DeviceRecord` 和 State Machine。
- 复用某个设备集成时，让它注册 Runtime Service，并向 Event Bus 发布规范化状态变化。
- 舍弃 HA 的独立 Web、Supervisor、Add-on、用户系统、完整配置流与本项目无关的集成。
- 若最终确实需要 HA 的大部分核心，应把它作为进程内基础设施模块封装在 Runtime 边界后；Agent 仍只使用 Facade，避免业务层反向耦合到 HA 内部 API。

## 当前工程边界

- Scheduler 在每次 `run` 和 Runtime `tick` 时执行到期任务，还不是独立后台线程。
- Runtime 状态随返回的 State 跨轮延续；SQLite 持久化、崩溃恢复和幂等迁移尚未实现。
- 模拟传感器可通过 `sensor.update` Service 注入变化；真实协议适配器尚未接入。
- 告警当前保存在 State 并产生事件，短信、电话、App Push 等通知通道尚未接入。
