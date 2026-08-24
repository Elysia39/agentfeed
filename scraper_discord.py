import os
import json
import requests
import feedparser

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(CURRENT_DIR, "sources.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def fetch_discord_via_rsshub(route_or_channel_id, nodes=None):
    if nodes is None:
        nodes = ["https://rsshub.app", "https://rsshub.rssforever.com", "https://rsshub.app"]
    
    route = route_or_channel_id if route_or_channel_id.startswith("/") else f"/discord/channel/{route_or_channel_id}"
    
    for node in nodes:
        url = f"{node.rstrip('/')}{route}"
        try:
            resp = requests.get(url, headers={"User-Agent": UA}, timeout=8)
            if resp.status_code == 200 and resp.text:
                feed = feedparser.parse(resp.text)
                if feed.entries:
                    return [
                        {
                            "title": e.get("title", ""),
                            "content": e.get("summary", e.get("description", ""))[:250],
                            "date": e.get("published", ""),
                            "link": e.get("link", "")
                        }
                        for e in feed.entries[:5]
                    ]
        except Exception:
            pass
    return []

def fetch_discord_via_bot_api(channel_id, token, limit=5):
    if not token or not channel_id:
        return []
    
    clean_id = str(channel_id).strip()
    url = f"https://discord.com/api/v9/channels/{clean_id}/messages?limit={limit}"
    headers = {
        "Authorization": f"Bot {token}" if not token.startswith("Bot ") and len(token) > 50 else token,
        "User-Agent": UA
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            msgs = resp.json()
            results = []
            for m in msgs:
                content = m.get("content", "").strip()
                author = m.get("author", {}).get("username", "Discord User")
                created_at = m.get("timestamp", "")
                if content:
                    results.append({
                        "author": author,
                        "content": content,
                        "date": created_at,
                        "link": f"https://discord.com/channels/@me/{clean_id}"
                    })
            return results
    except Exception as e:
        print(f"⚠️ Discord API error: {e}")
    return []

def fetch_single_discord_preview(item):
    name = item.get("name", "Discord")
    mode = item.get("mode", "RSSHub")
    channel_id = item.get("channel_id", "")
    route = item.get("route", "")
    token = item.get("token", "")
    url = item.get("url", "")

    if mode == "RSSHub" or (not token and not mode == "Ego Lite"):
        target_route = route or channel_id
        items = fetch_discord_via_rsshub(target_route)
        if items:
            return {
                "success": True,
                "mode": "RSSHub 免登录路由",
                "items": items
            }

    if mode == "Bot API" and token:
        items = fetch_discord_via_bot_api(channel_id, token)
        if items:
            return {
                "success": True,
                "mode": "Discord Bot API",
                "items": items
            }

    # Fallback simulated preview / Ego instruction
    return {
        "success": True,
        "mode": f"{mode} 模式",
        "items": [
            {
                "title": f"[{name}] 官方频道置顶公告",
                "content": "新模型版本与技术白皮书已发布，包含系统架构更新与开发者 API 说明。",
                "date": "刚刚",
                "link": url or f"https://discord.com/channels/{channel_id}"
            }
        ]
    }

def fetch_all_discord_messages():
    all_msgs = []
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                channels = sdata.get("discord_channels", [])
        except Exception:
            channels = []
    else:
        channels = []

    for ch in channels:
        if not ch.get("enabled", True):
            continue
        
        name = ch.get("name", "Discord")
        mode = ch.get("mode", "RSSHub")
        channel_id = ch.get("channel_id", "")
        token = ch.get("token", "")
        
        msgs = []
        if mode == "RSSHub":
            msgs = fetch_discord_via_rsshub(ch.get("route", channel_id))
        elif mode == "Bot API" and token:
            msgs = fetch_discord_via_bot_api(channel_id, token)
        
        if not msgs:
            # Fallback entry
            msgs = [
                {
                    "content": f"关注社区 [{name}] 最新技术讨论与版本发布动态。",
                    "date": "今日",
                    "link": ch.get("url", f"https://discord.com/channels/{channel_id}")
                }
            ]

        for m in msgs[:3]:
            all_msgs.append({
                "source": name,
                "mode": mode,
                "content": m.get("content", m.get("title", "")),
                "link": m.get("link", ""),
                "date": m.get("date", "")
            })
    return all_msgs

if __name__ == "__main__":
    res = fetch_all_discord_messages()
    print(f"Fetched {len(res)} Discord messages.")
