# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

飞书聊天机器人 → DeepSeek AI 解析 → 串口 → BMS 设备。

用户在飞书群发送自然语言指令（可带参数），DeepSeek 将其翻译为 BMS CLI 命令，通过串口发送到下游设备，再回复结果到飞书。

## 核心链路

```
飞书消息 → POST /feishu/webhook → 先回 200（避免飞书超时重试）
  → 后台线程: DeepSeek 解析 → 串口发送 → 飞书回复
```

## 架构原则

**所有中文→CLI 映射全部在 `intent.py` 的 `SYSTEM_PROMPT` 中完成，不写硬编码 if/switch。** 新增指令只需在 Prompt 里加一行中文描述，不用改任何逻辑代码。`SYSTEM_PROMPT` 就是整个翻译系统的规则书。

## 关键文件

| 文件 | 职责 |
|------|------|
| `main.py` | Flask 入口，串口收发，消息去重，后台线程 |
| `config.py` | `.env` 加载配置 |
| `intent.py` | DeepSeek 意图解析，**SYSTEM_PROMPT 是映射核心** |
| `feishu_bot.py` | 飞书 API（Token 缓存、签名验证、消息解析、回复） |
| `serial_ctrl.py` | 串口封装（备用，实际串口逻辑在 main.py） |

## CLI 指令参考文档

| 文件 | 内容 |
|------|------|
| `instruction-1.md` | 系统与状态查询（help/info/task/fault） |
| `instruction-2.md` | 仿真与极限测试（sim/inj/bal） |
| `instruction-3.md` | 算法标定与库管理（calib/est） |
| `instruction-4.md` | 硬件控制与系统命令（force/sys） |
| `instruction-5.md` | 参数读写与日志配置（get/set/loglevel/log） |
| `parameter-1.md` | 系统运行参数表（阈值型参数） |
| `parameter-2.md` | 系统运行参数表（U32 数值型参数） |
| `instruction-summary.md` | **当前完整的 58 条指令映射汇总（人类可读）** |

> 修改 `intent.py` 的 SYSTEM_PROMPT 后，应同步更新 `instruction-summary.md`。

## API 端点

| 路由 | 方法 | 用途 |
|------|------|------|
| `/feishu/webhook` | POST | 飞书事件回调（需外网穿透） |
| `/health` | GET | 健康检查 |
| `/test/bms` | POST | 本地测试：`{"cmd": "help"}` 直接发串口 |

## 环境变量（`.env`）

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `SERIAL_PORT` | 串口号，默认 COM3 |
| `SERIAL_BAUDRATE` | 波特率，默认 115200 |
| `FEISHU_APP_ID` | 飞书应用 ID |
| `FEISHU_APP_SECRET` | 飞书应用密钥 |
| `FLASK_PORT` | Flask 监听端口，默认 8080 |

## 通信协议

- 115200 bps 8N1
- PC → 设备：CLI 指令 + `\r\n`
- 循环读取多行回复直到超时（2s），超时返回 `TIMEOUT`
- 启动时 `dsrdtr=False` 禁用 DTR，防止 STM32 自动复位

## 调试

- 所有 webhook 请求的完整日志写入 `webhook_debug.log`（已在 `.gitignore`）
- 启动 Flask 时使用 `use_reloader=False`，避免重载导致串口重复连接

## DeepSeek 解析原则

**灵活理解，而非固定映射。** 用户可以用自然语言描述操作，DeepSeek 负责从中提取 CLI 指令和参数。

例如：
- 「第 0 节电池 SOC 改为 95%」→ `sim soc 0 95`
- 「查看所有命令」→ `help`
- 「设置过压阈值为 4200」→ `pack_ov 4200`

## 常用命令

```bash
pip install -r requirements.txt
python main.py
curl -X POST http://localhost:5000/test/bms -H "Content-Type: application/json" -d "{\"cmd\":\"help\"}"
```
