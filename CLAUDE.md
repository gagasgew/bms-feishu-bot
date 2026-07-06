# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

飞书聊天机器人 → DeepSeek AI 意图解析 → 串口 → STM32F405 控制 LED 亮灭。Windows PC 作为桥梁运行 Python 服务，通过 ngrok 内网穿透接收飞书回调。

## 核心链路

```
飞书消息 → POST /feishu/webhook → parse_message() → parse_intent(DeepSeek)
→ serial.send_command() → STM32 UART 接收 → GPIO 控制 LED → 回复 "LED ON/OFF"
→ send_message() 回复飞书用户
```

## 关键文件职责

| 文件 | 职责 |
|------|------|
| `main.py` | Flask 入口，`/feishu/webhook` 回调、`/health`、`/test/led` |
| `config.py` | `python-dotenv` 加载 `.env`，导出所有配置常量 |
| `intent.py` | DeepSeek API（OpenAI SDK 兼容），System Prompt 约束输出 `1`/`0`/`-1` |
| `serial_ctrl.py` | `SerialController` 单例，`send_command()` 发单字节并 `readline()` 等待回复 |
| `feishu_bot.py` | tenant_access_token 缓存获取、消息解析、签名验证（当前放行）、消息发送 |
| `firmware/main.c` | STM32 HAL 固件，阻塞接收 UART 单字节，`'1'`→GPIO_SET / `'0'`→GPIO_RESET |

## 通信协议（PC ↔ STM32）

- 115200 bps 8N1
- PC 发送单字节 ASCII：`'1'`（开灯）或 `'0'`（关灯）
- STM32 回复 `"LED ON\r\n"` 或 `"LED OFF\r\n"`
- 超时 1 秒返回 `"TIMEOUT"`

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（开发模式，debug=True）
python main.py

# 本地串口测试（绕过飞书）
curl -X POST http://localhost:8080/test/led -H "Content-Type: application/json" -d "{\"cmd\":\"1\"}"

# 健康检查
curl http://localhost:8080/health

# 内网穿透（飞书回调需要公网 URL）
ngrok http 8080

# 语法检查所有 Python 文件
python -m py_compile config.py; python -m py_compile intent.py; python -m py_compile serial_ctrl.py; python -m py_compile feishu_bot.py; python -m py_compile main.py
```

## 配置说明

所有敏感凭据在 `.env` 文件中，由 `config.py` 通过 `python-dotenv` 加载：

- `DEEPSEEK_API_KEY` — DeepSeek API 密钥
- `SERIAL_PORT` — STM32 串口号（默认 COM3）
- `FEISHU_APP_ID` / `FEISHU_APP_SECRET` — 飞书企业自建应用凭据
- `FLASK_PORT` — 服务端口（默认 8080）

`.env` 已加入 `.gitignore`，不会被提交。

## 部署前需手动完成

1. 填写 `.env` 中的真实凭据
2. 飞书开放平台创建企业自建应用，订阅 `im.message.receive_v1` 事件
3. 启动 ngrok，将公网 URL 填入飞书事件订阅回调地址
4. STM32 烧录 `firmware/main.c`（需 CubeMX 先生成 HAL 框架再替换）

## 注意事项

- `command.py` 是原始原型代码，保留但不参与主链路
- `feishu_bot.py` 签名验证当前直接返回 `True`，正式部署需按飞书加密配置调整
- DeepSeek API 调用使用 `temperature=0.0`，确保输出确定性
- 串口连接失败不会阻断 Flask 启动，飞书消息收发仍可测试
