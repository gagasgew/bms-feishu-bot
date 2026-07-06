# 飞书聊天控制 STM32 LED 灯 — 设计方案

> 日期：2026-06-11
> 状态：待评审

## 项目概述

通过飞书聊天消息远程控制 STM32F405 单片机上的 LED 灯亮灭。用户在飞书群中 @机器人发送自然语言指令（如"开灯"、"屋里好黑"），系统用大模型解析意图后通过串口控制硬件。

## 参考项目

工科男孙老师视频：树莓派 + OpenClaw + 摄像头 + 舵机 + 飞书聊天。本项目是其简化版：PC 替代树莓派，STM32F405 替代舵机控制板，LED 替代舵机，先把核心链路跑通。

---

## 整体架构

```
┌──────────┐  飞书消息API   ┌─────────────────────┐    UART/串口     ┌──────────────┐
│  飞书用户  │ ────────────▶ │   Windows PC          │ ──────────────▶ │  STM32F405   │
│  (手机/PC) │ ◀──────────── │  (Python 服务，常开)   │ ◀────────────── │  (HAL 固件)   │
└──────────┘  飞书回复API   │                       │  115200 bps     │              │
                           │ 1. Flask 收飞书Webhook │                 │ LED 亮/灭    │
                           │ 2. DeepSeek 解析意图   │                 │              │
                           │ 3. PySerial 发指令     │                 │              │
                           └─────────────────────┘                 └──────────────┘
```

**数据流**：
1. 用户在飞书群 @机器人发消息 → 飞书回调 → `POST /feishu/webhook`
2. Python 服务提取文本 → DeepSeek API 意图解析 → 返回 `"1"`(开灯) / `"0"`(关灯) / `"-1"`(无关)
3. 有效指令 → PySerial 通过串口发一个字节给 STM32
4. STM32 收到字节 → 控制 GPIO → LED 亮/灭 → 回复确认字符串
5. Python 调飞书 API 回复用户操作结果

**硬件清单**：
| 器件 | 用途 |
|------|------|
| Windows PC | 运行 Python 服务，需保持开机 |
| STM32F405 开发板 | 执行 LED 控制 |
| USB 转 TTL 模块 | 串口通信（若开发板不自带） |
| LED + 限流电阻(220Ω~1kΩ) | 被控对象 |
| 杜邦线若干 | 接线 |

---

## 模块一：飞书机器人接入

### 注册与配置

1. 飞书开放平台 (open.feishu.cn) 创建「企业自建应用」
2. 开启机器人能力，获取 **App ID** + **App Secret**
3. 权限配置：
   - `im:message:read_as_bot` — 读取群消息
   - `im:message:send_as_bot` — 回复消息
4. 事件订阅：`im.message.receive_v1`，回调地址指向本服务的公网 URL
5. 开发期用 **ngrok** 或 **frp** 内网穿透，暴露本地 Flask 端口

### 消息格式

飞书回调 POST body（简化）：
```json
{
  "event": {
    "type": "im.message.receive_v1",
    "message": {
      "chat_id": "oc_xxx",
      "content": "{\"text\":\"开灯\"}"
    }
  }
}
```

### 安全验证

- 飞书回调携带 `X-Lark-Request-Timestamp` + `X-Lark-Signature`
- 服务端用 App Secret 验签，防止伪造请求

---

## 模块二：意图解析（DeepSeek）

### 设计

沿用 `command.py` 中已验证的逻辑：

- **System Prompt**：`你是单片机控制大脑。用户意图是开灯，仅回复数字 1；意图是关灯，仅回复数字 0；其他闲聊，仅回复 -1。不要解释，不要输出任何额外内容。`
- **temperature = 0**：消除随机性，保证同一输入稳定输出
- **超时处理**：API 调用失败时默认返回 `-1`，不误操作硬件

### 费用估算

DeepSeek V3 定价极低（约 ¥1/百万 token），每次调用输入约 100 token、输出 1 token，单次成本约 ¥0.0001。日常使用基本免费。

---

## 模块三：串口通信

### PC 端（Python）

```python
import serial

ser = serial.Serial('COM3', 115200, timeout=1)

def send_command(cmd: str) -> str:
    """发送指令并读取单片机回复"""
    ser.write(cmd.encode('utf-8'))       # 发送 '0' 或 '1'
    response = ser.readline().decode().strip()  # 读取回复
    return response  # "LED ON" 或 "LED OFF"
```

- 串口号通过配置文件指定，不同机器只需改配置
- timeout=1s：1秒内未收到回复则超时

### 协议

| 方向 | 内容 | 含义 |
|------|------|------|
| PC → STM32 | `0x31` (ASCII '1') | 开灯 |
| PC → STM32 | `0x30` (ASCII '0') | 关灯 |
| STM32 → PC | `"LED ON\r\n"` | 开灯确认 |
| STM32 → PC | `"LED OFF\r\n"` | 关灯确认 |

使用 ASCII 而非二进制协议，便于用串口助手调试。

---

## 模块四：STM32 固件

### 开发环境

- **IDE**：STM32CubeIDE
- **框架**：HAL 库
- **配置工具**：STM32CubeMX 图形化引脚分配

### CubeMX 配置要点

| 外设 | 配置 |
|------|------|
| USART1（或其他） | Mode: Asynchronous, Baud: 115200, Word: 8bit, Stop: 1 |
| GPIO Output | 连接 LED 的引脚，推挽输出，默认低电平 |

### 固件逻辑（伪代码）

```c
// main.c 核心逻辑
uint8_t rx_byte;

while (1) {
    // 阻塞等待一个字节
    HAL_UART_Receive(&huart1, &rx_byte, 1, HAL_MAX_DELAY);

    if (rx_byte == '1') {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET);     // LED 亮
        HAL_UART_Transmit(&huart1, (uint8_t*)"LED ON\r\n", 8, 100);  // 回复确认
    }
    else if (rx_byte == '0') {
        HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET);   // LED 灭
        HAL_UART_Transmit(&huart1, (uint8_t*)"LED OFF\r\n", 9, 100);
    }
    // 其他字节忽略
}
```

---

## 模块五：Python 服务

### 项目结构

```
E:\cc-study\
├── config.py          # 配置：API Key、串口号、飞书凭据
├── feishu_bot.py      # 飞书消息收发 + 验签
├── intent.py          # DeepSeek 意图解析
├── serial_ctrl.py     # 串口通信
├── main.py            # Flask 主入口 + 路由
├── requirements.txt   # 依赖清单
└── .env               # 敏感凭据（不提交）
```

### 依赖

```
flask
openai
pyserial
requests
python-dotenv
pycryptodome          # 飞书验签可能需要
```

### main.py 路由

```
POST /feishu/webhook   →  飞书回调入口（验签 → 解析 → 发串口 → 回复）
GET  /health            →  健康检查
```

### 启动方式

```bash
python main.py
# Flask 监听 0.0.0.0:8080
# ngrok http 8080 → 获得公网 URL → 填入飞书开放平台事件回调地址
```

---

## 安全注意事项

1. **凭据管理**：API Key、App Secret 存入 `.env` 文件，不提交 Git
2. **飞书验签**：必须校验回调签名，拒绝伪造请求
3. **串口独占**：同一时刻只有一个进程打开串口，注意异常时释放
4. **LLM 安全**：System Prompt 将输出约束为 `0`/`1`/`-1` 三个值，防注入

---

## 开发顺序

| 步骤 | 内容 | 预计耗时 |
|------|------|---------|
| 1 | STM32CubeIDE 配引脚 + 写固件、烧录、串口助手验证 | 30min |
| 2 | `serial_ctrl.py` + Python 串口测试 | 15min |
| 3 | 飞书开放平台注册应用、配置权限 | 20min |
| 4 | `feishu_bot.py` + Flask Webhook | 30min |
| 5 | 串联全部模块 + ngrok 联调 | 20min |
| 6 | 整理代码、写 README | 10min |

---

## 后续扩展方向（本期不做）

- 加更多外设：舵机、继电器、温湿度传感器
- 加更多聊天平台：Telegram、企业微信
- 加 Web 控制面板作为备选
- STM32 端支持查询状态（发 `?` 回复当前灯的状态）
- 用 ESP32 替代 PC 串口方案，实现独立联网
