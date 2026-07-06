"""
主入口 — Flask HTTP 服务
提供飞书 Webhook 端点，串联意图解析 → 串口控制 → 飞书回复
"""
import json
import threading
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

# ── 已处理消息 ID 集合（防止飞书重试导致重复回复）──
_processed_ids: set[str] = set()
_MAX_ID_CACHE = 1000  # 最多缓存 1000 条，防止内存泄漏


def _is_duplicate(msg_id: str) -> bool:
    """检查消息是否已处理过，首次出现返回 False 并记录"""
    if msg_id in _processed_ids:
        return True
    _processed_ids.add(msg_id)
    # 超过上限时清空旧缓存
    if len(_processed_ids) > _MAX_ID_CACHE:
        _processed_ids.clear()
    return False

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
    """发送 CLI 指令字符串到串口，返回设备回复"""
    global _ser
    if _ser is None or not _ser.is_open:
        return "ERROR: 串口未连接"
    try:
        _ser.reset_input_buffer()          # 清空缓冲区
        _ser.write((cmd + "\r\n").encode("utf-8"))
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
    msg_id = msg.get("message_id", "")

    # ── 去重：同一消息 ID 只处理一次 ──
    if _is_duplicate(msg_id):
        log_entry += f"  结果: 重复消息 {msg_id}, 跳过\n"
        with open("webhook_debug.log", "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
        print(log_entry)
        return jsonify({"code": 0})

    print(f"[消息] 收到: {user_text}")

    # 先返回 200 给飞书，慢操作放到后台线程避免超时重试导致重复回复
    def _process():
        cmd, desc = parse_intent(user_text)
        log_entry_inner = log_entry + f"  用户文本: {user_text}, 意图: {desc}, 命令: {cmd}\n"

        if cmd == "-1":
            log_entry_inner += "  结果: 未识别指令\n"
            send_message(chat_id, "未识别该指令，请尝试使用功能描述，如「查看所有命令列表」「打印系统体检报告」等")
        else:
            try:
                result = serial_send(cmd)
                log_entry_inner += f"  串口结果: {result}\n"
                reply = f"指令: {cmd} ({desc})\n设备回复: {result}"
                send_message(chat_id, reply)
                log_entry_inner += f"  回复: {reply}\n"
            except Exception as e:
                send_message(chat_id, f"发送失败: {e}")
                log_entry_inner += f"  异常: {e}\n"

        with open("webhook_debug.log", "a", encoding="utf-8") as f:
            f.write(log_entry_inner + "\n")
        print(log_entry_inner)

    threading.Thread(target=_process, daemon=True).start()

    return jsonify({"code": 0})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "feishu-bms-cli"})


@app.route("/test/bms", methods=["POST"])
def test_bms():
    """本地测试端点：发送 BMS CLI 指令到串口"""
    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify({"error": "invalid json"}), 400
    cmd = data.get("cmd", "")
    if not cmd or not isinstance(cmd, str):
        return jsonify({"error": "cmd is required (string)"}), 400
    result = serial_send(cmd)
    return jsonify({"cmd": cmd, "result": result})


if __name__ == "__main__":
    print(f"[主程序] 飞书 BMS CLI 指令服务启动中...")
    print(f"   端口: {config.FLASK_PORT}")
    print(f"   串口: {config.SERIAL_PORT}")
    print("-" * 50)
    _init_serial()
    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=True, use_reloader=False)
