# STM32F103C8T6 LED 控制器 — 固件使用说明

## CubeMX 配置步骤

1. 打开 STM32CubeIDE，新建 STM32 项目，选择你的芯片型号（STM32F103C8Tx）

2. **USART1 配置**（PC ↔ STM32 通信）：
   - 左侧 Pinout → 点击 USART1 → Mode: **Asynchronous**
   - 自动分配引脚：PA9(TX), PA10(RX)
   - 右侧 Configuration → Baud Rate: **115200**, Word Length: 8, Stop Bits: 1

3. **GPIO 配置**（LED 引脚）：
   - 选择你要接 LED 的引脚（如 PC13 是多数板子的板载 LED）
   - 设为 **GPIO_Output**，默认电平 **Low**
   - 如用其他引脚，修改 `main.c` 中的 `LED_PORT` 和 `LED_PIN` 宏

4. 生成代码（Ctrl+S 或 Project → Generate Code）

5. 将本目录的 `main.c` 复制到 `Core/Src/main.c`，替换自动生成的文件
   - ⚠️ 注意：替换后要确保 `MX_USART1_UART_Init()` 和 `MX_GPIO_Init()` 函数名
     与 CubeMX 生成的一致（通常就是这两个名字）

6. 编译烧录：Project → Build All → Run → Debug

## 接线

| STM32 | 连接 | USB-TTL 模块 |
|-------|------|-------------|
| PA9 (TX) | → | RXD |
| PA10 (RX) | ← | TXD |
| GND | — | GND |

| STM32 | 连接 | LED |
|-------|------|-----|
| PC13 (LED_PIN) | → 限流电阻(220Ω~1kΩ) → LED 正极 | |
| GND | → LED 负极 | |

> 如果板子自带 USB 转串口芯片（如 CH340），直接用 USB 线连电脑即可，不需要额外的 USB-TTL 模块。

## 串口助手验证

烧录后，用串口助手（如 SSCOM、Putty）连接对应 COM 口（115200 bps），发送：
- 发送 `1` → LED 应亮，返回 `LED ON`
- 发送 `0` → LED 应灭，返回 `LED OFF`
- 发送其他字符 → 无响应（符合预期）
