"""
意图解析模块
调用 DeepSeek API 将用户的自然语言消息转换为控制指令
"""
from openai import OpenAI
import config

# DeepSeek 客户端（全局复用）
_client = OpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url=config.DEEPSEEK_BASE_URL,
)

# System Prompt：严格约束输出格式
_SYSTEM_PROMPT = (
    "你是一个单片机底层控制大脑。"
    "用户的输入可能是闲聊，也可能是控制指令。"
    "如果用户意图是开灯或常亮，仅回复数字 1；"
    "如果用户意图是关灯，仅回复数字 0；"
    "如果用户意图是呼吸灯（闪烁、渐变、呼吸、pwm），仅回复数字 2；"
    "如果是其他闲聊，仅回复 -1。"
    "注意：绝不要解释，绝不要输出任何额外标点符号或换行。"
)


def parse_intent(user_message: str) -> tuple[str, str]:
    """
    解析用户消息的控制意图

    参数:
        user_message: 用户发送的自然语言文本

    返回:
        (指令, 说明)
        - ('1', '开灯')
        - ('0', '关灯')
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

        if command == "1":
            return "1", "开灯"
        elif command == "0":
            return "0", "关灯"
        elif command == "2":
            return "2", "呼吸灯"
        else:
            return "-1", "非控制指令"

    except Exception as e:
        print(f"[意图] DeepSeek API 调用出错: {e}")
        return "-1", f"API 错误: {e}"
