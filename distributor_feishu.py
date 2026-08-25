import os
import json
import requests
import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
from paths import SOURCES_FILE

def load_feishu_config():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                return sdata.get("distribution_settings", {}).get("feishu", {
                    "enabled": False,
                    "webhook_url": ""
                })
        except Exception:
            pass
    return {"enabled": False, "webhook_url": ""}

def build_feishu_card(curated_data):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    now_str = datetime.datetime.now().strftime("%H:%M")
    lead = curated_data.get("lead_summary", "")
    macro = curated_data.get("macro_indicators", [])
    categories = curated_data.get("categories", {})
    sec_filings = curated_data.get("sec_filings", [])

    elements = []
    
    # Lead Note
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"📅 发布时间: {today_str} {now_str} | AgentFeed 智能提炼"
            }
        ]
    })

    # Lead summary
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**📌 今日核心速览：**\n{lead}"
        }
    })
    elements.append({"tag": "hr"})

    # Macro summary line
    if macro:
        macro_text = "📊 **重点数据与指标追踪：**\n"
        for m in macro[:6]:
            macro_text += f"• {m.get('name')}: **{m.get('value')}** ({m.get('change')})\n"
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": macro_text
            }
        })
        elements.append({"tag": "hr"})

    # Categories
    for cat_name, items in categories.items():
        if not items:
            continue
        cat_text = f"🔥 **{cat_name}**\n"
        for itm in items[:3]:
            title = itm.get('title', '')
            facts = itm.get('facts', itm.get('summary', ''))
            impact = itm.get('impact', '')
            link = itm.get('link', '')
            tags = itm.get('tags', itm.get('tickers', []))
            
            cat_text += f"• **[{title}]({link})**\n"
            if facts:
                cat_text += f"  - 核心事实: {facts}\n"
            if impact:
                cat_text += f"  - 关键洞察: {impact}\n"
            if tags:
                cat_text += f"  - 标签: `{' '.join(tags)}`\n"
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": cat_text
            }
        })
        elements.append({"tag": "hr"})

    # Public web button
    public_url = "https://feed.your-domain.com"
    elements.append({
        "tag": "action",
        "actions": [
            {
                "tag": "button",
                "text": {
                    "tag": "plain_text",
                    "content": "📖 在线阅读完整全源简报看板 ↗"
                },
                "type": "primary",
                "url": public_url
            }
        ]
    })

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📰 【AgentFeed 每日简报】{today_str} 全源热点与核心洞察"
                },
                "template": "blue"
            },
            "elements": elements
        }
    }
    return card

def send_feishu_brief(curated_data, custom_webhook=None):
    cfg = load_feishu_config()
    webhook = (custom_webhook or cfg.get("webhook_url", "")).strip()
    
    if not webhook:
        return {"success": False, "error": "飞书 Webhook URL 未配置"}
        
    card_payload = build_feishu_card(curated_data)
    
    try:
        resp = requests.post(webhook, json=card_payload, timeout=10)
        res_data = resp.json() if resp.status_code == 200 else {}
        if resp.status_code == 200 and res_data.get("StatusCode", 0) == 0:
            print("✅ 飞书群机器人推送成功！")
            return {"success": True, "message": "已成功推送到飞书群！"}
        else:
            err_msg = res_data.get("msg", resp.text)
            print(f"⚠️ 飞书推送失败: {err_msg}")
            return {"success": False, "error": f"飞书返回错误: {err_msg}"}
    except Exception as e:
        print(f"⚠️ 飞书网络异常: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    dummy_data = {
        "lead_summary": "测试数据：美联储维持基准利率预期，英伟达发布新一代算力平台。",
        "macro_indicators": [{"name": "美债 10Y", "value": "4.25%", "change": "+0.02%"}],
        "sec_filings": [{"ticker": "NVDA", "form": "8-K", "description": "重大战略合同签署"}],
        "categories": {
            "AI算力与前沿科技": [
                {"title": "OpenAI 推出全新推理模型", "facts": "计算效率提升3倍", "link": "https://openai.com"}
            ]
        }
    }
    print("Feishu card preview generated.")
