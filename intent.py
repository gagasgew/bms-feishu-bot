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

# System Prompt：BMS CLI 指令映射表
_SYSTEM_PROMPT = (
    "你是一个 BMS CLI 指令翻译器。根据用户输入的中文功能描述，输出对应的英文指令名。"
    "映射规则：\n"
    "1. 查询/查看/读取类操作 → 对应 get（读取参数）或 info（体检报告）或 fault（故障）或 task（任务）或 est（估算参数）或 log（黑匣子）\n"
    "2. 修改/设置/保存/写入/标定类操作 → 对应 set（修改参数）或 calib（标定）或 loglevel（日志级别）\n"
    "3. 控制/强控/接管类操作 → 对应 force（继电器）或 bal（均衡）或 inj（偏移注入）或 sim（仿真）\n"
    "4. 复位/重启/恢复类操作 → sys\n"
    "5. 查看所有命令 → help\n"
    "\n"
    "具体指令对照：\n"
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
    "读取参数 / 获取配置 / 查询阈值 / 查看参数 / 读阈值 → get\n"
    "修改参数 / 设置配置 / 保存阈值 / 写入阈值 / 修改并保存 → set\n"
    "改日志级别 / 调整打印级别 / 0到3 → loglevel\n"
    "读黑匣子 / 清除故障快照 / Flash日志 → log\n"
    "\n"
    "关键区分：「读取/获取/查询/查看」→ get；「修改/设置/保存/写入」→ set。"
    "遇到「修改」「保存」字眼一定是 set，不是 get。"
    "如果是其他无关内容，仅回复 -1。"
    "注意：只输出英文指令名或 -1，绝不要解释，绝不要输出任何额外标点符号或换行。"
)

# 指令 → 中文说明映射
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

        desc = _CMD_MAP.get(command)
        if desc:
            return command, desc
        else:
            return "-1", "非控制指令"

    except Exception as e:
        print(f"[意图] DeepSeek API 调用出错: {e}")
        return "-1", f"API 错误: {e}"
