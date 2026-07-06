"""
主入口 — Flask HTTP 服务
提供飞书 Webhook 端点，串联意图解析 → 串口控制 → 飞书回复
"""
import json

from flask import Flask, request, jsonify

import config
from intent import parse_intent
from serial_ctrl import get_serial
from feishu_bot import (
    verify_signature,
    parse_message,
    send_message,
)

app = Flask(__name__)


# ── 启动时连接串口 ──
try:
    get_serial().connect()
except Exception as e:
    print(f"[启动] 串口连接失败: {e}")
    print("[启动] 串口功能不可用，但飞书消息收发仍可测试")


@app.route("/feishu/webhook", methods=["POST"])
def feishu_webhook():
    """
    飞书事件回调入口

    飞书会 POST 到该端点，body 中包含消息事件。
    收到消息 → 解析意图 → 控制硬件 → 回复用户
    """
    body = request.get_json(force=True, silent=True)
    if body is None:
        return jsonify({"error": "invalid json"}), 400

    # 飞书开放平台首次配置事件回调时，会发送 challenge 验证
    if body.get("type") == "url_verification":
        challenge = body.get("challenge", "")
        print(f"[飞书] URL 验证 challenge: {challenge}")
        return jsonify({"challenge": challenge})

    # 验签（开发阶段先放行）
    timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
    nonce = request.headers.get("X-Lark-Request-Nonce", "")
    if not verify_signature(timestamp, nonce, json.dumps(body, ensure_ascii=False)):
        return jsonify({"error": "signature verification failed"}), 403

    # 解析消息
    msg = parse_message(body)
    if msg is None:
        # 不是文本消息，直接返回 200 避免飞书重试
        return jsonify({"code": 0})

    chat_id = msg["chat_id"]
    user_text = msg["text"]

    print(f"[消息] 收到: 「{user_text}」")

    # 意图解析
    cmd, desc = parse_intent(user_text)

    if cmd == "-1":
        # 非控制指令 → 回复提示
        send_message(chat_id, f"没理解您的意思😅\n您可以跟我说「开灯」或「关灯」")
    else:
        # 有效指令 → 发串口控制硬件
        try:
            result = get_serial().send_command(cmd)
            if "ON" in result:
                send_message(chat_id, f"✅ 灯已打开")
            elif "OFF" in result:
                send_message(chat_id, f"🌙 灯已关闭")
            else:
                send_message(chat_id, f"⚠️ 硬件无响应（{result}）")
        except Exception as e:
            print(f"[硬件] 控制失败: {e}")
            send_message(chat_id, f"❌ 硬件控制失败: {e}")

    return jsonify({"code": 0})


@app.route("/health", methods=["GET"])
def health():
    """健康检查端点"""
    return jsonify({"status": "ok", "service": "feishu-stm32-led"})


# ── 本地串口测试端点（可选） ──
@app.route("/test/led", methods=["POST"])
def test_led():
    """
    本地测试端点：绕过飞书，直接发指令
    curl -X POST http://localhost:8080/test/led -H "Content-Type: application/json" -d "{\"cmd\":\"1\"}"
    """
    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify({"error": "invalid json"}), 400

    cmd = data.get("cmd", "")
    if cmd not in ("0", "1"):
        return jsonify({"error": "cmd must be '0' or '1'"}), 400

    try:
        result = get_serial().send_command(cmd)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print(f"🚀 飞书 STM32 LED 控制服务启动中...")
    print(f"   端口: {config.FLASK_PORT}")
    print(f"   串口: {config.SERIAL_PORT}")
    print(f"   Webhook: http://localhost:{config.FLASK_PORT}/feishu/webhook")
    print(f"   健康检查: http://localhost:{config.FLASK_PORT}/health")
    print(f"   本地测试: http://localhost:{config.FLASK_PORT}/test/led")
    print("-" * 50)

    app.run(
        host="0.0.0.0",
        port=config.FLASK_PORT,
        debug=True,
    )
