/**
 * STM32F405 LED 串口控制 — 固件主程序
 *
 * 功能：
 *   从 USART1 接收单字节指令：
 *      '1' (0x31) → LED 亮  → 回复 "LED ON\r\n"
 *      '0' (0x30) → LED 灭  → 回复 "LED OFF\r\n"
 *   其他字节 → 忽略
 *
 * 使用前需在 CubeMX 中配置：
 *   1. USART1: Mode=Asynchronous, Baud=115200, 8N1
 *   2. PC13 (或你选的 LED 引脚): GPIO_Output, 推挽输出
 *   3. 生成代码后，将本文件替换自动生成的 main.c
 */

#include "main.h"

/* ── 引脚别名（根据实际接线修改） ── */
#define LED_PORT  GPIOC
#define LED_PIN   GPIO_PIN_13   /* 常见板载 LED 在 PC13 */

/* ── 外设句柄（CubeMX 自动生成） ── */
extern UART_HandleTypeDef huart1;

/* ── 函数声明 ── */
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART1_UART_Init(void);

/* ── 主函数 ── */
int main(void)
{
    uint8_t rx_byte;

    /* CubeMX 生成的初始化 */
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();
    MX_USART1_UART_Init();

    /* 发送启动消息，方便调试 */
    char *boot_msg = "STM32F405 LED Controller Ready\r\n";
    HAL_UART_Transmit(&huart1, (uint8_t *)boot_msg, strlen(boot_msg), 100);

    while (1)
    {
        /* 阻塞等待接收 1 个字节（无超时，串口有数据才返回） */
        HAL_UART_Receive(&huart1, &rx_byte, 1, HAL_MAX_DELAY);

        if (rx_byte == '1')
        {
            HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);     /* LED 亮 */
            char *msg = "LED ON\r\n";
            HAL_UART_Transmit(&huart1, (uint8_t *)msg, 8, 100);
        }
        else if (rx_byte == '0')
        {
            HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);  /* LED 灭 */
            char *msg = "LED OFF\r\n";
            HAL_UART_Transmit(&huart1, (uint8_t *)msg, 9, 100);
        }
        /* 其他字节 → 忽略 */
    }
}
