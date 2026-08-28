# ESPHome Host 数字设备环境与联调手册

本目录把客厅灯、窗帘、人体存在传感器和空调作为四个独立的 ESPHome Host
进程运行在 Ubuntu Docker 中。它保留 ESPHome 设备应用层组件和 Native API
链路，但不模拟 ESP32 CPU、GPIO 电气特性或真实机械/热力硬件。

本文是当前两轮搭建和排障工作的可复现版本。所有命令默认在 Ubuntu 24.04 VM
中执行；Windows 侧命令会单独标注。

## 1. 当前结论与已知环境

已经验证过的环境如下：

- Ubuntu 24.04.4 LTS，2 vCPU，约 7.7 GiB RAM；
- Docker 29.5.3；
- ESPHome 2026.8.1；
- 四个 Host 节点分别映射到 VM 的 TCP 6053～6056；
- VM 的 VMware NAT 地址曾为 `192.168.111.134`；
- Windows 宿主机直接使用 VMware 地址 `192.168.111.134`，无需 Tailscale；
- `172.17.0.1`、`172.18.0.1` 是 Docker bridge 地址，不用于宿主机连接。

端口约定：

| VM 端口 | Docker 服务 | ESPHome 实体 |
|---:|---|---|
| 6053 | `light-node` | Living Room Light |
| 6054 | `curtain-node` | Living Room Curtain |
| 6055 | `ac-node` | Living Room AC、Living Room Temperature |
| 6056 | `presence-node` | Living Room Presence |

容器内部都监听 Native API 默认端口 6053，Compose 负责映射不同的 VM 端口。
ESPHome Host 不通过 mDNS 自动发现，因此 Home Assistant 中必须手工填写地址和端口。

## 2. 仓库内容

```text
infra/esphome/
├── .env.example
├── .gitignore
├── compose.yaml
├── esphome/
│   ├── ac.yaml
│   ├── curtain.yaml
│   ├── light.yaml
│   ├── presence.yaml
│   └── secrets.example.yaml
└── scripts/
    ├── check_remote.ps1
    ├── reset_demo.sh
    └── validate.sh
```

`secrets.yaml`、编译缓存和 `.esphome` 生成目录均被忽略，不能提交真实密钥。

## 3. 从零准备 Ubuntu VM

### 3.1 检查资源和 Docker

```bash
uname -a
free -h
df -h
nproc
docker --version
docker compose version
sudo systemctl status docker --no-pager
```

如果普通用户执行 Docker 出现：

```text
permission denied while trying to connect to /var/run/docker.sock
```

不要长期进入 `sudo -i`。把当前用户加入 Docker 组，再重新登录：

```bash
sudo usermod -aG docker "$USER"
newgrp docker
docker ps
```

如果新组仍未生效，注销后重新登录。加入 `docker` 组等价于授予较高的系统权限，
只应对可信的开发账号这样配置。

### 3.2 获取项目并进入正确目录

```bash
git clone -b feat/embedded-home-runtime https://github.com/M1kasu/Care_Home_Agent.git
cd Care_Home_Agent/infra/esphome
pwd
```

后续命令必须在 `infra/esphome` 目录执行。之前出现 `/config/light.yaml: No such
file or directory`，原因就是进入 `sudo -i` 后工作目录变成了 `/root`，使 `$PWD`
挂载了错误目录。

### 3.3 固定镜像版本并生成 Native API 密钥

```bash
cp .env.example .env
cp esphome/secrets.example.yaml esphome/secrets.yaml
API_KEY="$(openssl rand -base64 32)"
sed -i "s|REPLACE_WITH_A_32_BYTE_BASE64_KEY|${API_KEY}|" esphome/secrets.yaml
chmod 600 esphome/secrets.yaml
```

确认密钥文件存在，但不要把输出发到公开频道：

```bash
test -s esphome/secrets.yaml && echo "secrets ready"
git check-ignore esphome/secrets.yaml
```

第二条应输出 `esphome/secrets.yaml`。

## 4. 校验、首次编译与启动

先拉取固定版本并检查 Compose：

```bash
docker compose pull
docker compose config
chmod +x scripts/*.sh
./scripts/validate.sh
```

四份配置都应出现：

```text
INFO Configuration is valid!
```

第一次 C++ 编译建议逐台执行，避免 2 vCPU VM 同时编译四份配置：

```bash
docker compose up light-node
```

看到节点启动并监听 API 后按 `Ctrl+C`，再依次构建其余节点：

```bash
docker compose up curtain-node
docker compose up presence-node
docker compose up ac-node
```

最后后台启动全部服务：

```bash
docker compose up -d
docker compose ps
docker compose logs --tail=100
```

期望看到四个容器为 `Up`，端口映射为：

```text
0.0.0.0:6053->6053/tcp
0.0.0.0:6054->6053/tcp
0.0.0.0:6055->6053/tcp
0.0.0.0:6056->6053/tcp
```

Ubuntu 本机检查：

```bash
ss -lnt | grep -E ':6053|:6054|:6055|:6056'
docker compose logs -f light-node
```

控制灯时，日志中的 `Brightness` 会变化；控制窗帘时会出现 `Motor: OPEN/CLOSE/STOP`；
空调处于制冷时温度会从 30.2 °C 向 26 °C 下降。这是加速的演示模型，不代表真实
房间的热力速度。

## 5. 从 Windows 宿主机访问 VM

### 5.1 当前本机 VMware 联调（首选）

Windows PowerShell：

```powershell
& .\infra\esphome\scripts\check_remote.ps1 -HostAddress 192.168.111.134
```

四个端口都显示 `Reachable=True` 后即可进行 Native API 握手。当前开发机已经实测
`192.168.111.134:6053～6056` 全部开放。

### 5.2 同一局域网（跨机器现场演示）

将 USB Wi-Fi 网卡透传给 Ubuntu VM，或把 VMware 网卡设为可直接进入现场局域网的
模式。确保 HA 主机与 VM 都拿到同一网段地址：

```bash
ip addr
hostname -I
```

在 HA 所在机器测试 `VM_LAN_IP:6053～6056`。同一 LAN 通常比远程 VPN 稳定、延迟低。

### 5.3 Tailscale（仅在确实跨公网时备用）

Ubuntu VM：

```bash
tailscale status
tailscale ip -4
tailscale netcheck
```

队友机器必须加入同一个 Tailnet，或接受该 VM 的 Machine Share。只在 Windows 宿主机
安装 Tailscale 并不保证另一台 HAOS 虚拟机可以访问 Tailnet；Tailscale 或正确的路由
必须存在于实际运行 Home Assistant 的网络环境中。

Windows PowerShell：

```powershell
tailscale status
tailscale ping 100.64.25.63
& .\infra\esphome\scripts\check_remote.ps1 -HostAddress 100.64.25.63
```

如果 `tailscale ping` 显示 `DERP (lax)`，说明在走洛杉矶中继。开发可继续，但最终
演示应改用同一 LAN，或检查双方 `tailscale netcheck` 的 `UDP`、NAT 和最近 DERP。

如果四个 `TcpTestSucceeded`/`Reachable` 不是全 `True`，先排查 Tailnet 分享、VM
防火墙和 Docker 端口，不要在 Home Assistant 中反复删除、重建设备。

## 6. Home Assistant Core 接入 ESPHome

官方 Home Assistant Core 自带 ESPHome Integration，能够通过持久的 Native API TCP
连接接收状态推送并控制设备。进入：

```text
Settings → Devices & services → Add Integration → ESPHome
```

逐个添加：

| Device | Host | Port | Encryption key |
|---|---|---:|---|
| Living Room Light | `192.168.111.134`（或 VM 当前 LAN IP） | 6053 | `secrets.yaml` 中的值 |
| Living Room Curtain | `192.168.111.134`（或 VM 当前 LAN IP） | 6054 | 同上 |
| Living Room AC | `192.168.111.134`（或 VM 当前 LAN IP） | 6055 | 同上 |
| Living Room Presence | `192.168.111.134`（或 VM 当前 LAN IP） | 6056 | 同上 |

不要填写 Docker 的 `172.17.x.x`/`172.18.x.x` 地址。添加后在 Developer Tools → States
确认实体 ID；通常会接近：

```text
light.living_room_light
cover.living_room_curtain
binary_sensor.living_room_presence
climate.living_room_ac
sensor.living_room_temperature
```

实体 ID 可能因历史配置出现后缀，后续脚本必须以 HA 页面显示的实际值为准。

## 7. 让 Care Home Agent 直接接入 ESPHome

项目使用 Home Assistant ESPHome Integration 底层的同一个官方客户端
`aioesphomeapi 45.6.1`。必须使用独立的 Python 3.11+ 环境，不升级系统 Python，
也不要复用队友已有的业务环境。在仓库根目录执行：

```powershell
# 队友首次准备
conda create -n CareHomeAgent python=3.11 pip -y
conda activate CareHomeAgent

# 当前开发机已有环境可改用：
# & E:\Anaconda\envs\CareHomeAgent\Scripts\Activate.ps1
python --version
python -m pip install -e ".[demo,test]" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu --prefer-binary
$env:PYTHONIOENCODING="utf-8"
$env:HOME_BACKEND="esphome"
$env:ESPHOME_HOST="192.168.111.134"
$env:ESPHOME_NOISE_PSK="从Ubuntu的esphome/secrets.yaml私下复制"
```

先做只读握手和实体发现：

```powershell
python scripts\check_esphome.py
```

成功结果应包含 `"ready": true`、四个节点的 `"connected": true`，以及灯、窗帘、
存在传感器、空调和温度的真实状态。当前开发环境已在 2026-08-29 实测四节点全部
连接成功，其中空调为 6055、人体存在为 6056。然后测试 Agent：

```powershell
python main.py "把客厅灯调到20%"
python main.py "把客厅窗帘关上"
python main.py "把客厅空调调到26度"
python demo\app.py
```

打开 `http://127.0.0.1:7860/`。快捷“观影模式”会通过真实 ESPHome 依次关闭窗帘、
把灯调到 15%，并将空调设为 26 °C。

不下载 GGUF 模型也能运行上述规则路径；需要本地模型时再执行：

```powershell
python scripts\download_model.py
```

### 实现边界

设置 `HOME_BACKEND=esphome` 后，调用链变为：

```text
Agent → HomeRuntime → ESPHomeIntegration → aioesphomeapi → Ubuntu ESPHome Host
```

集成维持后台 asyncio 连接、订阅设备主动推送，并把真实状态规范化到 Runtime。当前真实
映射范围是本目录的四个客厅节点；其他房间设备、网络诊断、提醒和能耗仍由
`SimulatorIntegration` 提供。独立 Home Assistant Core 仍可同时作为调试 UI 接入这些节点，
但不再是当前项目控制 ESPHome 的必经路径。

## 8. 在 HA 层做闭环联调

先在 Home Assistant 个人资料页创建 Long-Lived Access Token。把地址、Token 和实际实体 ID
只放在本机环境变量中，不要提交：

```powershell
$env:HA_URL="http://HA_HOST:8123"
$env:HA_TOKEN="YOUR_LONG_LIVED_ACCESS_TOKEN"
$headers = @{ Authorization = "Bearer $env:HA_TOKEN" }
```

读取灯状态：

```powershell
Invoke-RestMethod -Headers $headers -Uri "$env:HA_URL/api/states/light.living_room_light"
```

把灯调到 20%：

```powershell
$headers["Content-Type"] = "application/json"
$body = @{ entity_id = "light.living_room_light"; brightness_pct = 20 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Headers $headers -Body $body `
  -Uri "$env:HA_URL/api/services/light/turn_on"
```

关闭窗帘：

```powershell
$body = @{ entity_id = "cover.living_room_curtain" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Headers $headers -Body $body `
  -Uri "$env:HA_URL/api/services/cover/close_cover"
```

设置空调：

```powershell
$body = @{ entity_id = "climate.living_room_ac"; hvac_mode = "cool" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Headers $headers -Body $body `
  -Uri "$env:HA_URL/api/services/climate/set_hvac_mode"

$body = @{ entity_id = "climate.living_room_ac"; temperature = 26 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Headers $headers -Body $body `
  -Uri "$env:HA_URL/api/services/climate/set_temperature"
```

每次控制后同时观察：

1. HA Developer Tools 中的实体状态；
2. Ubuntu 上 `docker compose logs -f <service>`；
3. 再次调用 `GET /api/states/<entity_id>` 的回读结果。

这三处一致，才证明走通了“HA 服务调用 → ESPHome Native API → 数字设备 → 状态回传”，
而不是只修改了某个 Python 字典。

## 9. 重置、停止与验收

重置演示初始状态：

```bash
./scripts/reset_demo.sh
```

停止但保留编译缓存：

```bash
docker compose down
```

不要为了普通重启删除 `cache/`。验收清单：

- 四份配置均通过 `config`；
- 四个容器均为 `Up`，6053～6056 均可达；
- HA 中出现五个预期实体且为 Available；
- 灯亮度、窗帘运动、空调模式/温度均能从 HA 控制；
- ESPHome 日志显示对应动作；
- HA 能回读最终状态；
- 重置脚本可恢复确定的演示初态；
- `git status` 不包含 `secrets.yaml` 或编译缓存。

## 10. 常见故障

| 现象 | 原因与处理 |
|---|---|
| Docker socket permission denied | 将可信开发用户加入 `docker` 组并重新登录 |
| `/config/*.yaml` 不存在 | 当前目录错误；回到 `infra/esphome` 再运行 Compose |
| `mode: False` / YAML 自动转布尔 | `OFF`、`ON` 等值加引号；本配置已用 `"COOL"` |
| HA 自动发现不到 | Host 平台预期行为；手工添加 IP、端口和 Noise PSK |
| TCP 端口全失败 | 当前本机先检查 VMware NAT/LAN 和 VM 防火墙，不是 API key 问题 |
| TCP 通但 HA 验证失败 | 检查 32-byte Base64 Encryption Key 是否完全一致 |
| Gradio 启动检查返回 502 | 更新到包含 localhost 代理绕过的代码；临时方案是同时设置 `NO_PROXY=127.0.0.1,localhost,::1` 和 `no_proxy` |
| 远程响应 0.4～1 秒 | 当前走 DERP 中继；现场切换同一 LAN |
| Agent 仍显示模拟状态 | 确认启动前设置了 `HOME_BACKEND=esphome`，并重启 Python 进程 |

## 11. 安全要求

- 不把真实 `secrets.yaml`、HA Token 或 Tailscale 邀请链接提交到 Git；
- 不将 6053～6056 直接做公网端口转发；
- 开发阶段通过受控 Tailnet/Machine Share，现场通过可信 LAN；
- 怀疑密钥泄露时重新生成密钥、重启节点，并在 HA 中重新配置凭据。
