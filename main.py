"""
主入口 — Flask HTTP 服务
提供飞书 Webhook 端点，串联意图解析 → 串口控制 → 飞书回复
"""
import json
import serial as pyserial

from flask import Flask, request, jsonify

import config
from intent import parse_intent
from feishu_bot import (
    verify_signature,
    parse_message,
    send_message,
)

app = Flask(__name__)

# ── 串口（启动时连接，避免 DTR 复位 STM32） ──
_ser = None


def _init_serial():
    global _ser
    try:
        _ser = pyserial.Serial(
            port=config.SERIAL_PORT,
            baudrate=config.SERIAL_BAUDRATE,
            timeout=config.SERIAL_TIMEOUT,
            dsrdtr=False,        # 关键：禁用 DTR，避免 STM32 自动复位
        )
        # 读掉启动消息
        import time
        time.sleep(0.3)
        boot = _ser.readline()
        if boot:
            print(f"[串口] STM32 启动: {boot.decode('utf-8').strip()}")
        print(f"[串口] 已连接 {config.SERIAL_PORT}")
    except Exception as e:
        print(f"[串口] 连接失败: {e}")


def serial_send(cmd):
    global _ser
    if _ser is None or not _ser.is_open:
        return "ERROR: 串口未连接"
    try:
        _ser.reset_input_buffer()          # 清空缓冲区
        _ser.write(cmd.encode("utf-8"))
        resp = _ser.readline()
        # 跳过启动消息
        if resp and b'Ready' in resp:
            resp = _ser.readline()
        if resp:
            return resp.decode("utf-8").strip()
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"


@app.route("/feishu/webhook", methods=["POST"])
def feishu_webhook():
    body = request.get_json(force=True, silent=True)

    # ── 调试日志 ──
    import datetime
    log_entry = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 收到请求\n"
    log_entry += f"  Headers: {dict(request.headers)}\n"
    log_entry += f"  Body: {json.dumps(body, ensure_ascii=False) if body else 'None'}\n"

    if body is None:
        log_entry += "  结果: 空body, 返回400\n"
        with open("webhook_debug.log", "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        print(log_entry)
        return jsonify({"error": "invalid json"}), 400

    if body.get("type") == "url_verification":
        challenge = body.get("challenge", "")
        log_entry += f"  类型: URL验证, challenge={challenge}\n"
        with open("webhook_debug.log", "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        print(f"[飞书] URL 验证 challenge: {challenge}")
        return jsonify({"challenge": challenge})

    timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
    nonce = request.headers.get("X-Lark-Request-Nonce", "")
    if not verify_signature(timestamp, nonce, json.dumps(body, ensure_ascii=False)):
        log_entry += "  结果: 签名验证失败, 返回403\n"
        with open("webhook_debug.log", "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        print(log_entry)
        return jsonify({"error": "signature verification failed"}), 403

    msg = parse_message(body)
    if msg is None:
        log_entry += "  结果: parse_message返回None(事件类型不匹配/非文本消息)\n"
        with open("webhook_debug.log", "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        print(log_entry)
        return jsonify({"code": 0})

    chat_id = msg["chat_id"]
    user_text = msg["text"]

    print(f"[消息] 收到: {user_text}")

    cmd, desc = parse_intent(user_text)
    log_entry += f"  用户文本: {user_text}, 意图: {desc}, 命令: {cmd}\n"

    if cmd == "-1":
        log_entry += "  结果: 未理解意图\n"
        send_message(chat_id, "没理解您的意思，您可以跟我说「开灯」、「关灯」或「呼吸灯」")
    else:
        try:
            result = serial_send(cmd)
            log_entry += f"  串口结果: {result}\n"
            if "BREATH" in result:
                send_message(chat_id, "已切换到呼吸灯模式")
                log_entry += "  回复: 呼吸灯\n"
            elif "ON" in result:
                send_message(chat_id, "灯已打开")
                log_entry += "  回复: 灯已打开\n"
            elif "OFF" in result:
                send_message(chat_id, "灯已关闭")
                log_entry += "  回复: 灯已关闭\n"
            else:
                send_message(chat_id, f"硬件无响应（{result}）")
                log_entry += f"  回复: 硬件无响应\n"
        except Exception as e:
            send_message(chat_id, f"硬件控制失败: {e}")
            log_entry += f"  异常: {e}\n"

    with open("webhook_debug.log", "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")
    print(log_entry)

    return jsonify({"code": 0})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "feishu-stm32-led"})


@app.route("/test/led", methods=["POST"])
def test_led():
    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify({"error": "invalid json"}), 400
    cmd = data.get("cmd", "")
    if cmd not in ("0", "1", "2"):
        return jsonify({"error": "cmd must be '0', '1' or '2'"}), 400
    result = serial_send(cmd)
    return jsonify({"result": result})


if __name__ == "__main__":
    print(f"[主程序] 飞书 STM32 LED 控制服务启动中...")
    print(f"   端口: {config.FLASK_PORT}")
    print(f"   串口: {config.SERIAL_PORT}")
    print("-" * 50)
    _init_serial()
    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=True, use_reloader=False)
