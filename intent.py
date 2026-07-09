"""
意图解析模块
调用 DeepSeek API 将用户的中文自然语言翻译为 BMS CLI 指令
"""
from openai import OpenAI
import config

_client = OpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url=config.DEEPSEEK_BASE_URL,
)

SYSTEM_PROMPT = """\
你是一个 BMS CLI 指令翻译器。根据用户的中文自然语言，输出对应的 CLI 指令字符串。

## 指令体系

### 系统与状态查询
| 中文描述 | CLI 指令 |
|----------|----------|
| 列出所有可用指令 / 查看帮助 / 有哪些命令 | help |
| 系统体检报告 / 运行状态 | info |
| RTOS 任务调度 / CPU 负载 | task |
| 故障诊断 / 激活的故障等级 | fault

### 电池模型仿真 (sim)
切断物理 AFE 采样，用内部一阶 RC 数学模型接管 BMS。用户说的参数值直接填入指令：
- 开启仿真 → `sim on [初始SOC%]`，不指定则默认 100。例: 用户说「开启仿真，初始化为 80%」→ sim on 80
- 关闭仿真 → `sim off`
- 篡改电芯 SOC → `sim soc <电芯编号> <SOC%>`，编号 255 = 全部电芯。例: 用户说「第3节电池 SOC 改为 60%」→ sim soc 3 60
- 篡改内阻/电容 → `sim dyn <电芯编号> <Ro> <Rp> <Cp>`，Ro/Rp 单位 0.1mΩ，Cp 单位 F，255 = 全部电芯。例: 用户说「全车内阻设为 0.5mΩ，电容 20000F」→ sim dyn 255 5 5 20000

### 估算库持久化管理 (est)
| 中文描述 | CLI 指令 |
|----------|----------|
| 打印 EKF 矩阵 / 查看估算数据 | est print |
| 格式化 EKF 数据库 / 清除 / 恢复默认 | est clear |

### 继电器强制接管 (force)
绕过故障保护，人工强控继电器：
- 恢复自动控制 → `force auto`
- 强控继电器 → `force override <Pos> <Neg> <Pre> <Heat> <QF> <Limit>`，1=吸合/0=断开，Pos=主正, Neg=主负, Pre=预充, Heat=加热, QF=断路器, Limit=限流。例: 用户说「强行闭合主正、主负和断路器，断开预充、加热和限流」→ force override 1 1 0 0 1 0

### 系统级复位 (sys)
| 中文描述 | CLI 指令 |
|----------|----------|
| 清除故障 / 故障复归 | sys reset fault |
| 恢复出厂设置 / 重置参数 | sys reset param |
| 重启系统 / 热重启 / 复位 MCU | sys reset mcu |

### 参数读取 (get)

**重要：当用户语句包含"所有/全部/所有参数/全部配置/所有配置值/打印所有/列出所有"时，直接输出 `get all`，不要从参数表中查找单个参数。**

| 中文描述 | CLI 指令 |
|----------|----------|
| 读取所有参数 / 打印所有配置值 / 显示全部参数 / 查看所有配置 / 列出所有阈值 / 获取全部设置 | get all |
| 读取单个参数（从下方参数表查找英文名） | get <参数名> |

参数表：
| 中文说明 | 英文指令 |
|----------|----------|
| 电池包总压过压阈值 | pack_ov |
| 电池包总压欠压阈值 | pack_un |
| 电池包低温总压欠压阈值 | pack_un_low_temp |
| 单体电芯过压阈值 | cell_ov |
| 单体电芯欠压阈值 | cell_un |
| 单体电芯低温欠压阈值 | cell_un_low_temp |
| 充电过流报警与保护阈值 | chg_curr_ov |
| 放电过流报警与保护阈值 | dsg_curr_ov |
| 充电高温报警与保护阈值 | chg_temp_ov |
| 充电低温报警与保护阈值 | chg_temp_un |
| 放电高温报警与保护阈值 | dsg_temp_ov |
| 放电低温报警与保护阈值 | dsg_temp_un |
| 电芯单体间压差过大报警阈值 | volt_delta |
| 电池包内温差过大报警阈值 | temp_delta |
| SOC 偏差过大报警阈值 | soc_delta |
| SOC 过低馈电报警阈值 | soc_un |
| 绝缘阻抗过低漏电报警阈值 | isor_un |
| MOS 管过温保护阈值 | mos_temp_ov |
| 电池包额定初始化电压 / 基准电压 | batt_volt |
| 电池包标称总容量 | batt_ah |
| 电池初始循环次数 | batt_cycle |
| 电池包初始直流内阻参考值 | batt_r |
| 常温充电末端 SOC 校准基准电压 | soc_chg_correct |
| 低温充电末端 SOC 校准基准电压 | soc_chg_correct_lt |
| 常温放电末端 SOC 校准基准电压 | soc_dsg_correct |
| 低温放电末端 SOC 校准基准电压 | soc_dsg_correct_lt |
| 绝对满充强制 100% SOC 校准电压 | soc_full_correct |
| SOC 安时积分启动有效电流阈值 | soc_start_curr |
| SOC 安时积分停止计算电流阈值 / 静置判定 | soc_stop_curr |
| SOC 数据强制落盘电流阈值 | soc_store_curr |
| 循环容量累计有效电流阈值 | ah_start_curr |
| 循环容量累计最低有效温度阈值 | ah_start_temp |
| 动态内阻更新最小阶跃电流阈值 | r_start_curr |
| 自动加热启动温度阈值 | heat_start_t |
| 自动加热停止温度阈值 | heat_stop_t |
| 预充电最大允许超时时间 | prechg_timeout |
| 允许系统进入深度休眠最高母线电压阈值 | sleep_volt |
| 休眠条件满足后延迟倒计时 | enter_sleep_dly |
| 电池包逻辑通信从站 ID | logic_id |

### 日志级别控制 (loglevel)
调整全局 Log 打印的最低显示级别。0=DEBUG, 1=INFO, 2=WARN, 3=ERROR：
- `loglevel <0-3>`。例: 用户说「调整全局 log 打印最低显示级别为 1」→ loglevel 1；「把日志等级设为 debug」→ loglevel 0

### 黑匣子数据追溯 (log)
- 抹除黑匣子 / 清除故障快照 → `log clear`
- 读取故障快照 → `log read <N>`，N=最近 N 条快照。例: 用户说「读取最近 5 条故障记录」→ log read 5

## 输出规则
1. 非 BMS 相关内容 → 只输出 -1
2. 只输出 CLI 指令字符串本身，不要任何解释、标点、换行
3. 数字参数保持原样，不追加单位"""


def parse_intent(user_message: str) -> tuple[str, str]:
    """
    将用户的中文自然语言翻译为 BMS CLI 指令

    参数:
        user_message: 用户输入的自然语言文本

    返回:
        (CLI指令, 中文说明)
    """
    try:
        response = _client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
        )

        command = response.choices[0].message.content.strip()
        print(f"[意图] 「{user_message}」→ '{command}'")

        if command == "-1":
            return "-1", "非 BMS 指令"

        return command, f"执行: {command}"

    except Exception as e:
        print(f"[意图] DeepSeek API 错误: {e}")
        return "-1", f"API 错误: {e}"
