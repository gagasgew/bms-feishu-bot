# CLAUDE.md

## 项目概述

飞书聊天机器人 → DeepSeek AI 解析 → 串口 → BMS 设备。

用户在飞书群发送自然语言指令（可带参数），DeepSeek 将其翻译为 BMS CLI 命令，通过串口发送到下游设备，再回复结果到飞书。

## 核心链路

```
飞书消息 → POST /feishu/webhook → 先回 200
  → 后台线程: DeepSeek 解析 → 串口发送 → 飞书回复
```

## 关键文件

| 文件 | 职责 |
|------|------|
| `main.py` | Flask 入口，串口收发，消息去重 |
| `config.py` | `.env` 加载配置 |
| `intent.py` | DeepSeek 意图解析，自然语言 → CLI 指令 |
| `feishu_bot.py` | 飞书 API（Token、消息解析、回复） |
| `serial_ctrl.py` | 串口封装（备用） |

## CLI 指令参考文档

这些 `.md` 文件是 BMS CLI 指令体系的完整参考，`intent.py` 的 SYSTEM_PROMPT 需与之一致：

| 文件 | 内容 |
|------|------|
| `instruction-1.md` | 系统与状态查询（help/info/task/fault） |
| `instruction-2.md` | 仿真与极限测试（sim/inj/bal） |
| `instruction-3.md` | 算法标定与库管理（calib/est） |
| `instruction-4.md` | 硬件控制与系统命令（force/sys） |
| `instruction-5.md` | 参数读写与日志配置（get/set/loglevel/log） |
| `parameter.md` | 系统运行参数表（batt_volt/soc_* 等） |

## DeepSeek 解析原则

**灵活理解，而非固定映射。** 用户可以用自然语言描述操作，DeepSeek 负责从中提取 CLI 指令和参数。

例如：
- 「第 0 节电池 SOC 改为 95%」→ `sim soc 0 95`
- 「查看所有命令」→ `help`
- 「设置过压阈值为 4200」→ `pack_ov 4200`

## 通信协议

- 115200 bps 8N1
- PC → 设备：CLI 指令 + `\r\n`
- 读取一行回复，超时 2s 返回 `TIMEOUT`
- 启动时禁用 DTR 防止设备复位

## 常用命令

```bash
pip install -r requirements.txt
python main.py
curl -X POST http://localhost:5000/test/bms -H "Content-Type: application/json" -d "{\"cmd\":\"help\"}"
```
