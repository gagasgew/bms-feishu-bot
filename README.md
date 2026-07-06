# 飞书聊天控制 STM32 LED 🎮💡

通过飞书群聊 @机器人 发送自然语言指令，远程控制 STM32F405 单片机上的 LED 灯亮灭。

## 效果演示

```
群聊中:
  👨 用户: @机器人 屋里好黑啊
  🤖 机器人: ✅ 灯已打开

  👨 用户: @机器人 我要睡觉了，关灯吧
  🤖 机器人: 🌙 灯已关闭

  👨 用户: @机器人 今天天气怎么样
  🤖 机器人: 没理解您的意思😅
```

## 系统架构

```
飞书 App → 飞书服务器 → frp/ngrok → PC(Python) → 串口 → STM32F405 → LED
                                ↑                      ↑
                           DeepSeek API          HAL 固件控制 GPIO
                          (意图解析)
```

## 硬件清单

| 器件 | 数量 | 说明 |
|------|------|------|
| STM32F405 开发板 | 1 | |
| USB-TTL 模块 | 1 | 若板子自带 CH340 则不需要 |
| LED + 220Ω 电阻 | 1 | 可用板载 LED |
| 杜邦线 | 若干 | |
| Windows PC | 1 | 需保持开机运行 Python 服务 |

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
```

### 3. STM32 烧录固件

详见 [`firmware/README.md`](firmware/README.md)：
- CubeMX 配置 USART1 (115200 bps) + LED GPIO
- 替换 `main.c` 后编译烧录
- 串口助手发 `1` 验证 LED 亮、发 `0` 验证 LED 灭

### 4. 启动服务

```bash
python main.py
```

输出：
```
🚀 飞书 STM32 LED 控制服务启动中...
   端口: 8080
   串口: COM3
   Webhook: http://localhost:8080/feishu/webhook
```

### 5. 内网穿透 + 飞书配置

```bash
# 用 ngrok 暴露本地 8080
ngrok http 8080

# 获得公网 URL，如 https://abc123.ngrok-free.app
# 复制到飞书开放平台 → 事件订阅 → 回调地址:
# https://abc123.ngrok-free.app/feishu/webhook
```

### 6. 测试

在飞书群聊中 @机器人 发送：
- 「开灯」「屋里好黑」「帮我开下灯」 → LED 亮
- 「关灯」「我要睡觉了」 → LED 灭
- 「你好」 → 提示无法理解

也可以用 curl 本地测试串口（不经过飞书）：
```bash
curl -X POST http://localhost:8080/test/led -H "Content-Type: application/json" -d "{\"cmd\":\"1\"}"
```

## 项目结构

```
E:\cc-study\
├── main.py               # Flask 主入口
├── config.py             # 配置管理（读取 .env）
├── intent.py             # DeepSeek 意图解析
├── serial_ctrl.py        # 串口通信封装
├── feishu_bot.py         # 飞书消息收发
├── requirements.txt      # Python 依赖
├── .env                  # 敏感凭据（不提交 Git）
├── .gitignore
├── firmware/             # STM32 固件代码
│   ├── main.c            # HAL 主程序
│   └── README.md         # 烧录说明
├── command.py            # 原始原型代码（保留）
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-11-feishu-stm32-led-design.md  # 设计文档
```

## 后续扩展方向

- 📹 加摄像头实现拍照回复
- ⚙️ 控制舵机 / 继电器
- 🌡️ 读取温湿度传感器数据
- 📱 同时支持 Telegram Bot
