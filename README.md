# 飞书 BMS CLI 指令服务 🔋💬

通过飞书群聊 @机器人 或私聊发送中文功能描述，自动映射为 BMS CLI 英文指令，经串口发送到下游设备。

## 效果演示

```
群聊中:
  👨 用户: @机器人 查看所有命令列表
  🤖 机器人: 指令: help (查看所有命令列表)
             设备回复: [BMS 设备返回的命令列表]

私聊中:
  👨 用户: 打印系统体检报告
  🤖 机器人: 指令: info (打印系统体检报告)
             设备回复: [BMS 设备返回的体检数据]

  👨 用户: 今天天气怎么样
  🤖 机器人: 未识别该指令，请尝试使用功能描述...
```

## 系统架构

```
飞书 App → 飞书服务器 → ngrok → PC(Python) → 串口 → BMS 设备
                                ↑
                           DeepSeek API
                          (中文→英文指令映射)
```

## 支持指令（15 条）

| 英文指令 | 中文描述 |
|----------|----------|
| `help` | 查看所有命令列表 |
| `info` | 打印系统体检报告 |
| `task` | 打印 RTOS 任务调度 |
| `fault` | 诊断故障等级 |
| `sim` | 开启电池模型仿真 |
| `inj` | 采集数据偏移注入 |
| `bal` | 控制硬件均衡通道 |
| `calib` | 强制标定 EKF 参数 |
| `est` | 打印/格式化 KVDB 参数 |
| `force` | 控制主回路继电器 |
| `sys` | 系统复位 |
| `get` | 读取配置参数 |
| `set` | 修改配置参数 |
| `loglevel` | 更改日志打印级别 |
| `log` | 读/清除黑匣子快照 |

> 详细使用说明见 `01_BMS 交互式控制台 (CLI) 详细使用说明.docx`

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `.env` 文件，填入你的凭据：

```env
DEEPSEEK_API_KEY=sk-你的API-Key
SERIAL_PORT=COM3            # 设备管理器里串口的 COM 号
FEISHU_APP_ID=cli_xxx       # 飞书开放平台获取
FEISHU_APP_SECRET=xxx       # 飞书开放平台获取
FLASK_PORT=5000
```

### 3. 启动服务

```bash
python main.py
```

### 4. 内网穿透 + 飞书配置

```bash
ngrok http 5000
```

获得公网 URL 后，填入飞书开放平台 → 事件订阅 → 回调地址：
`https://xxx.ngrok-free.app/feishu/webhook`

### 5. 测试

在飞书群聊中 @机器人 或直接私聊机器人发送中文功能描述即可。

本地测试（不经过飞书）：

```bash
curl -X POST http://localhost:5000/test/bms \
  -H "Content-Type: application/json" \
  -d "{\"cmd\":\"help\"}"
```

## 项目结构

```
├── main.py               # Flask 主入口（webhook / 去重 / 后台线程）
├── config.py             # 配置管理（读取 .env）
├── intent.py             # DeepSeek 意图解析（15条指令映射）
├── feishu_bot.py         # 飞书消息收发（群聊+私聊）
├── serial_ctrl.py        # 串口通信封装（备用）
├── 指令1.md              # 15 条 CLI 指令中英文对照表
├── requirements.txt      # Python 依赖
└── .env                  # 敏感凭据（不提交 Git）
```
