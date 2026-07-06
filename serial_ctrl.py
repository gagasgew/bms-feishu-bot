"""
串口通信模块
负责与 STM32F405 通过 UART 收发指令
"""
import serial
import config


class SerialController:
    """串口控制器，管理 PC ↔ STM32 的通信"""

    def __init__(self):
        self._ser = None

    def connect(self):
        """打开串口连接"""
        self._ser = serial.Serial(
            port=config.SERIAL_PORT,
            baudrate=config.SERIAL_BAUDRATE,
            timeout=config.SERIAL_TIMEOUT,
        )
        print(f"[串口] 已连接 {config.SERIAL_PORT} @ {config.SERIAL_BAUDRATE} bps")

    def disconnect(self):
        """关闭串口连接"""
        if self._ser and self._ser.is_open:
            self._ser.close()
            print("[串口] 已断开")

    def send_command(self, cmd: str) -> str:
        """
        发送控制指令并读取单片机回复

        参数:
            cmd: '0'（关灯）或 '1'（开灯）

        返回:
            单片机回复字符串，如 "LED ON" / "LED OFF"
            超时时返回 "TIMEOUT"
        """
        if self._ser is None or not self._ser.is_open:
            return "ERROR: 串口未连接"

        self._ser.write(cmd.encode("utf-8"))
        print(f"[串口] 已发送: '{cmd}'")

        response_bytes = self._ser.readline()
        if response_bytes:
            response = response_bytes.decode("utf-8").strip()
            print(f"[串口] 收到回复: '{response}'")
            return response
        else:
            print("[串口] 等待回复超时")
            return "TIMEOUT"


# 全局单例
_serial_ctrl: SerialController | None = None


def get_serial() -> SerialController:
    """获取全局 SerialController 实例（懒加载）"""
    global _serial_ctrl
    if _serial_ctrl is None:
        _serial_ctrl = SerialController()
    return _serial_ctrl
