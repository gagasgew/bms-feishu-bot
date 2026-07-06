# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

飞书聊天机器人 → DeepSeek AI 意图解析 → 串口 → BMS 设备。

用户在飞书群发送中文功能描述（如「查看所有命令列表」），DeepSeek 映射为 BMS CLI 英文指令（如 `help`），通过串口发送 `help\r\n` 到下游设备，再将设备回复返回飞书。

## 核心链路

```
飞书消息 → POST /feishu/webhook → parse_message()
  → return 200（毫秒级，避免飞书超时重试）
  → 后台线程: parse_intent(DeepSeek) → serial_send() → send_message() 回复
```

三个关键设计：
- **后台线程处理**：DeepSeek + 串口可能耗时 2-3 秒，先回 200 再异步处理，防止飞书超时重试
- **message_id 去重**：`_processed_ids` 集合缓存已处理的消息 ID，飞书重试同一消息时直接跳过
- **群聊 + 私聊双模式**：同一条 `im.message.receive_v1` 事件同时覆盖群聊 @机器人 和私聊直接发消息，代码无需区分

## 关键文件职责

| 文件 | 职责 |
|------|------|
| `main.py` | Flask 入口，`/feishu/webhook`（核心路由）、`/health`、`/test/bms`，串口初始化和发送、消息去重 |
| `config.py` | `python-dotenv` 加载 `.env`，导出所有配置常量 |
| `intent.py` | DeepSeek API，System Prompt 包含 15 条 BMS CLI 中英文映射，`parse_intent()` 返回 `(英文指令, 中文说明)` |
| `feishu_bot.py` | tenant_access_token 缓存、消息解析（`parse_message` 返回 chat_id/message_id/text）、签名验证（当前放行）、消息发送 |
| `serial_ctrl.py` | `SerialController` 单例，BMS CLI 串口封装（备用，`main.py` 自管串口） |
| `指令1.md` | 15 条 BMS CLI 指令中英文对照表（Markdown 表格） |

## 通信协议（PC → 串口设备）

- 115200 bps 8N1
- PC 发送：CLI 指令字符串 + `\r\n`，如 `help\r\n`、`info\r\n`
- 读取一行回复（`readline()`）
- 超时 2 秒返回 `"TIMEOUT"`
- 启动时禁用 DTR（`dsrdtr=False`）防止设备复位

## 15 条 CLI 指令映射

见 `指令1.md` 完整表格。DeepSeek System Prompt（`intent.py`）中包含完整的中文描述 → 英文指令映射。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py

# 本地测试（绕过飞书）
curl -X POST http://localhost:5000/test/bms -H "Content-Type: application/json" -d "{\"cmd\":\"help\"}"

# 健康检查
curl http://localhost:5000/health

# 内网穿透
ngrok http 5000

# 语法检查
python -m py_compile config.py intent.py main.py feishu_bot.py serial_ctrl.py
```

## 配置说明

所有敏感凭据在 `.env` 中，由 `config.py` 加载：

- `DEEPSEEK_API_KEY` — DeepSeek API 密钥
- `SERIAL_PORT` — 串口号（当前 COM7）
- `FEISHU_APP_ID` / `FEISHU_APP_SECRET` — 飞书企业自建应用凭据
- `FLASK_PORT` — 服务端口（当前 5000）

`.env` 已加入 `.gitignore`。

## 部署前需手动完成

1. 填写 `.env` 中的真实凭据
2. 飞书开放平台创建企业自建应用，订阅 `im.message.receive_v1` 事件
3. 启动 ngrok，将公网 URL 填入飞书事件订阅回调地址（`https://xxx.ngrok-free.app/feishu/webhook`）

## 注意

- `feishu_bot.py` 签名验证直接返回 `True`，正式部署需按飞书加密配置调整
- DeepSeek API 使用 `temperature=0.0`，确保输出确定性
- 串口连接失败不会阻断 Flask 启动，飞书消息收发仍可测试
- `debug=True` 但 `use_reloader=False`，避免重载时重复初始化串口
