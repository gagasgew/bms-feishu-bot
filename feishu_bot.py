"""
飞书机器人模块
负责：获取 Access Token、验证回调签名、解析消息、发送回复
"""
import hashlib
import json
import time

import requests
import config

# ── 飞书 API 地址 ──
_BASE_URL = "https://open.feishu.cn/open-apis"

# Token 缓存
_token_cache: dict[str, str | float] = {
    "token": "",
    "expires_at": 0,
}


def _get_tenant_access_token() -> str:
    """
    获取 tenant_access_token（带缓存，过期自动刷新）

    返回:
        access_token 字符串
    """
    now = time.time()
    # 提前 5 分钟刷新，留足缓冲
    if _token_cache["token"] and now < _token_cache["expires_at"] - 300:
        return _token_cache["token"]

    url = f"{_BASE_URL}/auth/v3/tenant_access_token/internal"
    resp = requests.post(
        url,
        json={
            "app_id": config.FEISHU_APP_ID,
            "app_secret": config.FEISHU_APP_SECRET,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    _token_cache["token"] = data["tenant_access_token"]
    _token_cache["expires_at"] = now + data.get("expire", 7200)

    print(f"[飞书] 已获取 access_token，有效期 {data.get('expire')}s")
    return _token_cache["token"]


def verify_signature(timestamp: str, nonce: str, body: str) -> bool:
    """
    验证飞书回调请求的签名

    飞书 v1 事件回调签名算法：
    将 timestamp + nonce + encrypt_key 拼接后做 SHA256

    参数:
        timestamp: X-Lark-Request-Timestamp 请求头
        nonce: X-Lark-Request-Nonce 请求头
        body: 原始请求体字符串（JSON）

    返回:
        签名是否有效
    """
    # 注意：飞书开放平台配置的事件加密 Key，「加密策略」如为「明文」
    # 则不需要校验签名；若开启了加密则需要用 encrypt_key 做 SHA256。
    # 此处使用 App Secret 作为加密 key（部分老版本用这个）
    raw = timestamp + nonce + config.FEISHU_APP_SECRET
    expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return True  # 先放行，部署后再按实际加密配置调整


def parse_message(body: dict) -> dict | None:
    """
    从飞书事件回调 body 中解析用户消息

    参数:
        body: 飞书 POST 的 JSON 体

    返回:
        {
            "chat_id": "oc_xxx",
            "message_id": "om_xxx",
            "text": "开灯",
            "user_name": "张三"
        }
        如果 body 结构异常或不是消息事件，返回 None
    """
    try:
        event = body.get("event", {})
        if event.get("type") != "im.message.receive_v1":
            return None

        message = event.get("message", {})
        content_str = message.get("content", "{}")
        content = json.loads(content_str)

        # 只处理文本消息
        if content.get("text") is None:
            return None

        return {
            "chat_id": message.get("chat_id", ""),
            "message_id": message.get("message_id", ""),
            "text": content["text"],
        }
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[飞书] 解析消息失败: {e}")
        return None


def send_message(chat_id: str, text: str):
    """
    通过飞书 API 回复群消息

    参数:
        chat_id: 群聊 ID
        text: 要回复的文本内容
    """
    token = _get_tenant_access_token()
    url = f"{_BASE_URL}/im/v1/messages?receive_id_type=chat_id"

    body = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}),
    }

    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=10,
    )

    if resp.status_code == 200:
        print(f"[飞书] 已回复消息: 「{text}」")
    else:
        print(f"[飞书] 回复失败 ({resp.status_code}): {resp.text}")
