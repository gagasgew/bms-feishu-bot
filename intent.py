"""
意图解析模块
调用 DeepSeek API 将用户的中文功能描述映射为 BMS CLI 英文指令
"""
from openai import OpenAI
import config

# DeepSeek 客户端（全局复用）
_client = OpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url=config.DEEPSEEK_BASE_URL,
)

# ── 参数名 → 中文说明映射（42 个 BMS 参数）──
_PARAM_DESC = {
    # 系统故障阈值参数（instruction-2.md）
    "pack_ov":          "电池包总压过压阈值",
    "pack_un":          "电池包总压欠压阈值",
    "pack_un_low_temp": "电池包低温状态下总压欠压阈值",
    "cell_ov":          "单体电芯过压阈值",
    "cell_un":          "单体电芯欠压阈值",
    "cell_un_low_temp": "单体电芯低温状态下欠压阈值",
    "chg_curr_ov":      "充电过流报警与保护阈值",
    "dsg_curr_ov":      "放电过流报警与保护阈值",
    "chg_temp_ov":      "充电高温报警与保护阈值",
    "chg_temp_un":      "充电低温报警与保护阈值",
    "dsg_temp_ov":      "放电高温报警与保护阈值",
    "dsg_temp_un":      "放电低温报警与保护阈值",
    "volt_delta":       "电芯单体间压差过大报警阈值",
    "temp_delta":       "电池包内温差过大报警阈值",
    "soc_delta":        "SOC 偏差过大报警阈值",
    "soc_un":           "电池组 SOC 过低（馈电）报警阈值",
    "isor_un":          "绝缘阻抗过低（漏电）报警阈值",
    "mos_temp_ov":      "功率板 MOS 管过温保护阈值",
    # 系统运行参数（instruction-3.md）
    "batt_volt":        "电池包额定初始化电压 / 基准电压",
    "batt_ah":          "电池包标称总容量 (安时)",
    "batt_cycle":       "电池初始循环次数 (Cycle)",
    "batt_r":           "电池包初始直流内阻参考值",
    "soc_chg_correct":      "常温充电末端 SOC 校准基准电压",
    "soc_chg_correct_lt":   "低温充电末端 SOC 校准基准电压",
    "soc_dsg_correct":      "常温放电末端 SOC 校准基准电压",
    "soc_dsg_correct_lt":   "低温放电末端 SOC 校准基准电压",
    "soc_full_correct":     "绝对满充强制 100% SOC 校准电压",
    "soc_start_curr":       "SOC 安时积分启动有效电流阈值",
    "soc_stop_curr":        "SOC 安时积分停止计算电流阈值（静置判定）",
    "soc_store_curr":       "触发 SOC 数据强制落盘（EEPROM）电流阈值",
    "ah_start_curr":        "循环容量（SOH）累计有效电流阈值",
    "ah_start_temp":        "循环容量（SOH）累计最低有效温度阈值",
    "r_start_curr":         "动态内阻更新允许的最小阶跃电流阈值",
    "heat_start_t":         "自动加热功能启动温度阈值",
    "heat_stop_t":          "自动加热功能停止温度阈值",
    "prechg_timeout":       "预充电阶段最大允许超时时间",
    "sleep_volt":           "允许系统进入深度休眠的最高母线电压阈值",
    "enter_sleep_dly":      "满足休眠条件后的延迟倒计时（防止频繁唤醒）",
    "beep_func":            "蜂鸣器功能硬件使能开关 (0:关, 1:开)",
    "button_type":          "外部物理按键类型配置 (0:自锁式, 1:自复位式)",
    "logic_id":             "电池包的逻辑/物理通信从站 ID",
    "heating_func":         "自动加热管理模块全局使能开关 (0:关, 1:开)",
}


def _build_system_prompt() -> str:
    """动态构建 System Prompt，包含完整参数名对照表"""
    fault_params = "\n".join(
        f"  {k} = {v}"
        for k, v in _PARAM_DESC.items()
        if k in {
            "pack_ov", "pack_un", "pack_un_low_temp",
            "cell_ov", "cell_un", "cell_un_low_temp",
            "chg_curr_ov", "dsg_curr_ov",
            "chg_temp_ov", "chg_temp_un", "dsg_temp_ov", "dsg_temp_un",
            "volt_delta", "temp_delta", "soc_delta", "soc_un",
            "isor_un", "mos_temp_ov",
        }
    )
    run_params = "\n".join(
        f"  {k} = {v}"
        for k, v in _PARAM_DESC.items()
        if k not in {
            "pack_ov", "pack_un", "pack_un_low_temp",
            "cell_ov", "cell_un", "cell_un_low_temp",
            "chg_curr_ov", "dsg_curr_ov",
            "chg_temp_ov", "chg_temp_un", "dsg_temp_ov", "dsg_temp_un",
            "volt_delta", "temp_delta", "soc_delta", "soc_un",
            "isor_un", "mos_temp_ov",
        }
    )

    return (
        "你是一个 BMS CLI 指令翻译器。根据用户输入的中文功能描述，输出对应的英文指令。\n"
        "\n"
        "=== 基础指令（直接输出指令名，不加参数）===\n"
        "查看所有命令列表 / 帮助 / 有哪些指令 → help\n"
        "打印系统体检报告 / 黑板状态 / 系统信息 / 当前状态 → info\n"
        "打印 RTOS 任务调度 / CPU负载 / 堆栈使用 → task\n"
        "诊断故障 / 激活的故障等级 / 故障信息 → fault\n"
        "开启电池仿真 / HIL测试 / 离线仿真 → sim\n"
        "采集数据偏移 / 注入故障 / 物理偏移 → inj\n"
        "控制硬件均衡 / 强控均衡 / 均衡开关 → bal\n"
        "强制标定 / 修改SOC / EKF矩阵 / 标定参数 → calib\n"
        "打印估算参数 / 格式化KVDB / EKF数据 → est\n"
        "控制继电器 / 强控主回路 / 接管继电器 → force\n"
        "系统复位 / 故障复归 / 恢复出厂 / 重启MCU → sys\n"
        "改日志级别 / 调整打印级别 / 0到3 → loglevel\n"
        "读黑匣子 / 清除故障快照 / Flash日志 → log\n"
        "\n"
        "=== 参数读写指令 ===\n"
        "读取规则：输出参数名本身即可（设备直接发参数名读取，无需 get 前缀）\n"
        "  规则1：用户说「查看/读取/查询/获取 + 参数中文名」→ 输出参数名\n"
        "  规则2（重要）：用户直接输入参数中文名（不带动词），默认当作读取 → 输出参数名\n"
        "  例如：「电芯单体间压差过大报警阈值」→ volt_delta\n"
        "  例如：「查看电池包总压过压阈值」→ pack_ov\n"
        "  例如：「循环容量（SOH）累计有效电流阈值」→ ah_start_curr\n"
        "修改规则：用户说「修改/设置/保存/写入 + 参数中文名 + 值」→ <参数名> <值>\n"
        "  例如：「设置电池包总压过压阈值为 4200」→ pack_ov 4200\n"
        "关键区分：「读取/获取/查询/查看」→ 裸参数名；「修改/设置/保存/写入」→ 参数名+值。\n"
        "遇到「修改」「保存」字眼一定带值，不是只读。\n"
        "\n"
        "【故障阈值参数】\n"
        f"{fault_params}\n"
        "\n"
        "【系统运行参数】\n"
        f"{run_params}\n"
        "\n"
        "=== 输出规则 ===\n"
        "1. 如果是无关内容，仅回复 -1\n"
        "2. 基础指令只输出指令名，如 help、info、fault\n"
        "3. 读参数只输出参数名本身（无 get 前缀），如 pack_ov、chg_curr_ov\n"
        "4. 写参数输出 参数名+空格+值，如 pack_ov 4200\n"
        "5. 绝不要输出任何额外解释、标点符号或换行\n"
    )


# 缓存 System Prompt
_SYSTEM_PROMPT = _build_system_prompt()

# 基础指令 → 中文说明映射
_CMD_MAP = {
    "help":     "查看所有命令列表",
    "info":     "打印系统体检报告",
    "task":     "打印 RTOS 任务调度",
    "fault":    "诊断故障等级",
    "sim":      "开启电池模型仿真",
    "inj":      "采集数据偏移注入",
    "bal":      "控制硬件均衡通道",
    "calib":    "强制标定 EKF 参数",
    "est":      "打印/格式化 KVDB 参数",
    "force":    "控制主回路继电器",
    "sys":      "系统复位",
    "get":      "读取配置参数",
    "set":      "修改配置参数",
    "loglevel": "更改日志打印级别",
    "log":      "读/清除黑匣子快照",
}


def parse_intent(user_message: str) -> tuple[str, str]:
    """
    解析用户消息，将中文描述映射为 BMS CLI 英文指令

    参数:
        user_message: 用户发送的自然语言文本（中文功能描述）

    返回:
        (指令, 说明) 元组
        - ('help', '查看所有命令列表')
        - ('get pack_ov', '读取电池包总压过压阈值')
        - ('set pack_ov 4200', '设置电池包总压过压阈值 → 4200')
        - ('-1', '非控制指令')
    """
    try:
        response = _client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
        )

        command = response.choices[0].message.content.strip()
        print(f"[意图] 用户说「{user_message}」→ 解析结果: '{command}'")

        if command == "-1":
            return "-1", "非控制指令"

        # 解析命令
        parts = command.split(maxsplit=1)
        first = parts[0].lower()

        # 1. 基础指令（如 help、info、sys 等）—— 直接查 _CMD_MAP
        if first in _CMD_MAP and first not in ("get", "set"):
            desc = _CMD_MAP[first]
            return command, desc

        # 2. 裸参数名 = 读取参数（如 chg_curr_ov、ah_start_curr）
        if command in _PARAM_DESC:
            param_desc = _PARAM_DESC[command]
            return command, f"读取{param_desc}"

        # 3. <参数名> <值> = 写参数（如 chg_curr_ov 50）
        if first in _PARAM_DESC:
            param_desc = _PARAM_DESC[first]
            value = parts[1] if len(parts) > 1 else "?"
            return command, f"设置{param_desc} → {value}"

        # 4. 兼容旧的 get/set 前缀
        if first in ("get", "set") and len(parts) > 1:
            param_parts = parts[1].split()
            param_name = param_parts[0]
            param_desc = _PARAM_DESC.get(param_name, param_name)
            if first == "get":
                return f"get {param_name}", f"读取{param_desc}"
            else:
                value = param_parts[1] if len(param_parts) > 1 else "?"
                return f"set {param_name} {value}", f"设置{param_desc} → {value}"

        # 未识别
        return "-1", "非控制指令"

    except Exception as e:
        print(f"[意图] DeepSeek API 调用出错: {e}")
        return "-1", f"API 错误: {e}"