/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
#include <math.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define LED_PORT  GPIOC
#define LED_PIN   GPIO_PIN_13

/* 呼吸灯参数 */
#define PWM_PERIOD_US    5000    /* PWM 周期 5ms（200Hz，无闪烁） */
#define BREATH_STEPS     100     /* 亮度步数 */
#define STEP_DURATION_MS 25      /* 每步持续时间，完整周期 = 100*25ms*2 = 5秒 */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART1_UART_Init(void);
/* USER CODE BEGIN PFP */
void DWT_Init(void);
void delay_us(uint32_t us);
void led_on(void);
void led_off(void);
void breathing_cycle(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* ── DWT 微秒延时（用于软件 PWM） ── */
void DWT_Init(void)
{
    /* 使能 DWT  cycle counter */
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}

void delay_us(uint32_t us)
{
    uint32_t start = DWT->CYCCNT;
    /* SystemCoreClock / 1e6 = 每微秒的 CPU 周期数 */
    uint32_t cycles = us * (SystemCoreClock / 1000000);
    while ((DWT->CYCCNT - start) < cycles)
    {
        /* 忙等 */
    }
}

/* ── LED 基本操作 ── */
void led_on(void)
{
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);
}

void led_off(void)
{
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);
}

/* ── 呼吸灯（软件 PWM，正弦曲线） ── */
void breathing_cycle(void)
{
    uint8_t rx_check;

    /* 一轮完整的 亮→灭→亮 呼吸 */
    for (int i = 0; i <= BREATH_STEPS; i++)
    {
        /* 正弦曲线：使亮度变化更自然 */
        float phase = (float)i / BREATH_STEPS;              /* 0 → 1 */
        float brightness = (sinf(phase * 3.1415926f - 1.5707963f) + 1.0f) / 2.0f;  /* 0→1 按正弦 */

        uint32_t on_us  = (uint32_t)(brightness * PWM_PERIOD_US);
        uint32_t off_us = PWM_PERIOD_US - on_us;

        uint32_t step_end = HAL_GetTick() + STEP_DURATION_MS;
        while (HAL_GetTick() < step_end)
        {
            if (on_us > 2)
            {
                led_on();
                delay_us(on_us);
            }
            if (off_us > 2)
            {
                led_off();
                delay_us(off_us);
            }

            /* 检查是否有新串口命令 */
            if (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_RXNE))
            {
                return;  /* 退出呼吸，回到主循环处理命令 */
            }
        }
    }

    /* 灭 → 亮 */
    for (int i = BREATH_STEPS; i >= 0; i--)
    {
        float phase = (float)i / BREATH_STEPS;
        float brightness = (sinf(phase * 3.1415926f - 1.5707963f) + 1.0f) / 2.0f;

        uint32_t on_us  = (uint32_t)(brightness * PWM_PERIOD_US);
        uint32_t off_us = PWM_PERIOD_US - on_us;

        uint32_t step_end = HAL_GetTick() + STEP_DURATION_MS;
        while (HAL_GetTick() < step_end)
        {
            if (on_us > 2)
            {
                led_on();
                delay_us(on_us);
            }
            if (off_us > 2)
            {
                led_off();
                delay_us(off_us);
            }

            if (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_RXNE))
            {
                return;
            }
        }
    }
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */
  uint8_t rx_byte;
  uint8_t mode = 0;  /* 0=停止, 1=常亮, 2=呼吸 */
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */

  /* 初始化 DWT  cycle counter（微秒延时用） */
  DWT_Init();

  /* 发送启动消息 */
  char *boot_msg = "STM32F103C8T6 LED Controller Ready\r\n"
                   "Commands: 1=ON  0=OFF  2=BREATH\r\n";
  HAL_UART_Transmit(&huart1, (uint8_t *)boot_msg, strlen(boot_msg), 100);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

    /* ── 先检查是否有串口命令到达 ── */
    if (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_RXNE))
    {
        HAL_UART_Receive(&huart1, &rx_byte, 1, 10);

        if (rx_byte == '1')
        {
            mode = 1;
            led_on();
            char *msg = "LED ON\r\n";
            HAL_UART_Transmit(&huart1, (uint8_t *)msg, 8, 100);
        }
        else if (rx_byte == '0')
        {
            mode = 0;
            led_off();
            char *msg = "LED OFF\r\n";
            HAL_UART_Transmit(&huart1, (uint8_t *)msg, 9, 100);
        }
        else if (rx_byte == '2')
        {
            mode = 2;
            char *msg = "LED BREATH\r\n";
            HAL_UART_Transmit(&huart1, (uint8_t *)msg, 12, 100);
        }
    }

    /* ── 呼吸模式 ── */
    if (mode == 2)
    {
        breathing_cycle();
    }
    /* mode 0/1 什么都不做，LED 状态已由 GPIO 保持 */

  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);

  /*Configure GPIO pin : PC13 */
  GPIO_InitStruct.Pin = GPIO_PIN_13;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
