import serial
from openai import OpenAI

# ---------------- 配置区 ----------------

# 1. 填写你的 DeepSeek API Key
DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"

# 2. 配置串口 (请根据设备管理器或 lsusb 实际显示的 COM 口 / ttyUSB 端口进行修改)
# 注意：测试纯代码逻辑时，可以先把它注释掉
# ser = serial.Serial('COM3', 115200, timeout=1)

# ---------------- 初始化 ----------------

# 初始化 DeepSeek 客户端 (利用 OpenAI 的 SDK)
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"  # 关键点：将请求地址重定向到 DeepSeek
)


def get_control_command(user_input):
    """调用 DeepSeek API 分析意图，返回控制指令"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # V3 模型，速度快且极度便宜
            messages=[
                {
                    "role": "system",
                    "content": "你是一个单片机底层控制大脑。用户的输入可能是闲聊，也可能是控制指令。如果用户意图是开灯，仅回复数字 1；如果意图是关灯，仅回复数字 0；如果是其他闲聊，仅回复 -1。注意：绝不要解释，绝不要输出任何额外标点符号或换行。"
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            temperature=0.0  # 关键点：温度设为0，消除大模型的随机性，保证每次相同的指令输出完全一致
        )

        # 提取并清理返回的指令
        command = response.choices[0].message.content.strip()
        return command

    except Exception as e:
        print(f"DeepSeek API 调用出错: {e}")
        return "-1"


# ---------------- 模拟运行流 ----------------

if __name__ == "__main__":
    # 假设这是从飞书 Webhook 接收到的消息
    feishu_messages = [
        "这屋里怎么这么黑啊",
        "帮我把灯关了吧，我要睡觉了",
        "今天天气真不错"
    ]

    for msg in feishu_messages:
        print(f"\n[飞书接收] 用户说: {msg}")

        # 1. 大脑思考：提取指令
        cmd = get_control_command(msg)
        print(f"[意图解析] DeepSeek 决定发送指令: '{cmd}'")

        # 2. 神经传导：通过串口下发给 STM32F103C8T6
        # if cmd in ['0', '1']:
        #     ser.write(cmd.encode('utf-8'))
        #     print(f"[硬件执行] 已向串口发送字节流: b'{cmd}'")