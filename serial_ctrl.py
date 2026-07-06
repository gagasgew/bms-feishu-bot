"""
串口通信模块
负责与 BMS 设备通过 UART 收发 CLI 指令

注意：当前 main.py 自管串口，本模块作为备用封装保留。
"""
import serial
import config


_ser = None


def _get_serial():
    """获取全局串口对象，按需连接"""
    global _ser
    if _ser is None or not _ser.is_open:
        _ser = serial.Serial(
            port=config.SERIAL_PORT,
            baudrate=config.SERIAL_BAUDRATE,
            timeout=config.SERIAL_TIMEOUT,
        )
        print(f"[串口] 已连接 {config.SERIAL_PORT} @ {config.SERIAL_BAUDRATE} bps")
    return _ser


def send_command(cmd: str) -> str:
    """
    发送 BMS CLI 指令并读取设备回复

    参数:
        cmd: BMS CLI 英文指令，如 'help'、'info'、'get'

    返回:
        设备回复字符串（去除末尾换行）
        超时时返回 "TIMEOUT"
        错误时返回 "ERROR: ..."
    """
    try:
        s = _get_serial()
        # BMS CLI 协议：指令 + 回车换行
        s.write((cmd + "\r\n").encode("utf-8"))
        print(f"[串口] 已发送: '{cmd}'")

        response_bytes = s.readline()
        if response_bytes:
            response = response_bytes.decode("utf-8").strip()
            print(f"[串口] 收到回复: '{response}'")
            return response
        else:
            print("[串口] 等待回复超时")
            return "TIMEOUT"
    except Exception as e:
        print(f"[串口] 错误: {e}")
        return f"ERROR: {e}"
