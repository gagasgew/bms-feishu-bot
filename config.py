"""
全局配置管理
从 .env 文件和环境变量中加载配置项
"""
import os
from dotenv import load_dotenv

load_dotenv()


# ── DeepSeek ──
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ── 串口 ──
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", "115200"))
SERIAL_TIMEOUT = 1.0  # 读超时(秒)

# ── 飞书 ──
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

# ── Flask ──
FLASK_PORT = int(os.getenv("FLASK_PORT", "8080"))
