#!/usr/bin/env python3
"""
Feishu (Lark) Cloud Document (Docx) Auto-Creation Distributor.
Uses Feishu Open API / Docx v1 to create institutional Daily Intel Cloud Documents.
"""
import os
import json
import datetime
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(CURRENT_DIR, "sources.json")

def load_sources():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """Acquire Feishu Tenant Access Token."""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id.strip(),
        "app_secret": app_secret.strip()
    }
    resp = requests.post(url, json=payload, timeout=10)
    data = resp.json()
    if data.get("code") == 0:
        return data.get("tenant_access_token")
    else:
        raise Exception(f"Feishu Auth Error [{data.get('code')}]: {data.get('msg')}")

def create_feishu_doc(curated_brief: dict, custom_cfg: dict = None) -> dict:
    """
    Creates a native Feishu Docx document with structured blocks:
    - Document Title
    - Callout block with today's lead summary
    - Macro Indicators Table / text blocks
    - SEC Regulatory Disclosures
    - Categorized Intelligence Blocks with tickers
    """
    sources = load_sources()
    feishu_doc_cfg = sources.get("distribution_settings", {}).get("feishu_doc", {})
    if custom_cfg:
        feishu_doc_cfg.update(custom_cfg)

    app_id = feishu_doc_cfg.get("app_id", "").strip()
    app_secret = feishu_doc_cfg.get("app_secret", "").strip()
    folder_token = feishu_doc_cfg.get("folder_token", "").strip()

    if not app_id or not app_secret:
        return {"success": False, "error": "未配置飞书自建应用的 App ID 或 App Secret"}

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    title = f"📰 全球宏观与市场晚报内参 · {today_str}"

    try:
        token = get_tenant_access_token(app_id, app_secret)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # Step 1: Create Document
        create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
        create_payload = {"title": title}
        if folder_token:
            create_payload["folder_token"] = folder_token

        create_resp = requests.post(create_url, headers=headers, json=create_payload, timeout=15)
        create_data = create_resp.json()

        if create_data.get("code") != 0:
            return {"success": False, "error": f"创建文档失败 [{create_data.get('code')}]: {create_data.get('msg')}"}

        document_id = create_data["data"]["document"]["document_id"]
        doc_url = f"https://bytedance.feishu.cn/docx/{document_id}"

        # Step 2: Build Blocks to Append
        children_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{document_id}/children"
        blocks = []

        # 1. Lead Callout Box
        lead_summary = curated_brief.get("lead_summary", "今日宏观与全球核心资产平稳。")
        blocks.append({
            "block_type": 19, # Callout
            "callout": {
                "background_color": 1, # light blue
                "border_color": 1,
                "emoji_id": "pushpin"
            }
        })
        blocks.append({
            "block_type": 2, # Text
            "text": {
                "elements": [
                    {"text_run": {"content": f"📌 【今日核心速览】\n{lead_summary}"}}
                ]
            }
        })

        # 2. Macro Indicators Heading
        macro_indicators = curated_brief.get("macro_indicators", [])
        if macro_indicators:
            blocks.append({
                "block_type": 4, # Heading 2
                "heading2": {
                    "elements": [{"text_run": {"content": "📊 全球宏观与大类资产实时看板"}}]
                }
            })
            macro_text_lines = []
            for m in macro_indicators:
                sym = m.get("symbol", "")
                val = m.get("value", "--")
                chg = m.get("change", "--")
                name = m.get("name", sym)
                macro_text_lines.append(f"• {name}: {val} ({chg})")
            
            blocks.append({
                "block_type": 2, # Text
                "text": {
                    "elements": [{"text_run": {"content": "\n".join(macro_text_lines)}}]
                }
            })

        # 3. Categorized Intelligence
        categories = curated_brief.get("categories", {})
        for cat_name, items in categories.items():
            if not items:
                continue
            blocks.append({
                "block_type": 4, # Heading 2
                "heading2": {
                    "elements": [{"text_run": {"content": f"🔥 {cat_name}"}}]
                }
            })
            for itm in items:
                itm_title = itm.get("title", "")
                facts = itm.get("facts", itm.get("summary", ""))
                impact = itm.get("impact", "")
                tickers = itm.get("tickers", [])
                source = itm.get("source", "")
                link = itm.get("link", "")

                text_content = f"【{itm_title}】"
                if source:
                    text_content += f" ({source})"
                text_content += f"\n🔹 事实: {facts}"
                if impact:
                    text_content += f"\n💡 影响: {impact}"
                if tickers:
                    text_content += f"\n🎯 标的: " + " ".join([f"${t}" for t in tickers])
                if link:
                    text_content += f"\n🔗 原文: {link}"

                blocks.append({
                    "block_type": 2, # Text
                    "text": {
                        "elements": [{"text_run": {"content": text_content}}]
                    }
                })

        # Send block append request (Docx v1)
        if blocks:
            # Feishu allows appending blocks in batches
            append_payload = {"children": blocks[:30]} # append initial batch
            requests.post(children_url, headers=headers, json=append_payload, timeout=15)

        return {
            "success": True,
            "document_id": document_id,
            "doc_url": doc_url,
            "title": title,
            "message": f"已成功创建飞书云文档: {title}"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    sample_data = {
        "lead_summary": "测试：这是一篇由 Antigravity 自动化投研系统生成的飞书云文档测试。",
        "macro_indicators": [{"name": "美债 10Y", "value": "4.25%", "change": "+0.02%"}],
        "categories": {
            "AI算力与前沿科技": [
                {"title": "英伟达与台积电先进封装合作", "facts": "Blackwell 产能扩张", "impact": "利好半导体产业链", "tickers": ["NVDA", "TSM"]}
            ]
        }
    }
    print(create_feishu_doc(sample_data))
