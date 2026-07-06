"""
串口通信模块
负责与 STM32F103C8T6 通过 UART 收发指令
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
    发送控制指令并读取单片机回复

    参数:
        cmd: '0'（关灯）或 '1'（开灯）

    返回:
        单片机回复字符串，如 "LED ON" / "LED OFF"
        超时时返回 "TIMEOUT"
    """
    try:
        s = _get_serial()
        s.write(cmd.encode("utf-8"))
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
