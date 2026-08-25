import os
import json
import glob
import subprocess
import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from scraper_rss import test_rsshub_latency, fetch_single_feed_preview
from scraper_sec import fetch_sec_filings_for_ticker
from scraper_macro import fetch_macro_indicators
from scraper_discord import fetch_single_discord_preview
from scraper_substack import fetch_substack_feed
from scraper_hn import fetch_single_hn_preview
from scraper_reddit import fetch_single_reddit_preview
from scraper_arxiv import fetch_single_arxiv_preview
from llm_curator import curate_daily_intel
from distributor_feishu import send_feishu_brief
from distributor_feishu_doc import create_feishu_doc
from distributor_obsidian import save_note_to_obsidian, get_obsidian_vaults
from distributor_email import send_email_brief
from paths import SOURCES_FILE, HISTORY_FILE, HTML_FILE, ICON_FILE, get_resource_path
import sys

app = FastAPI(
    title="AgentFeed - Universal Perception & Ingestion Framework for AI Agents",
    description="AgentFeed: Open-Source Multi-Source Information Perception, LLM Curation, and Multi-Channel Distribution Hub for AI Agents.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_sources():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sources: {e}")
    return {
        "channel_toggles": {
            "rss": True, "web": True, "blog": True, "tg": True, "dc": True,
            "sub": True, "wx": True, "hn": True, "reddit": True, "arxiv": True, "sec": True
        },
        "rsshub_instances": {},
        "llm_settings": {},
        "distribution_settings": {},
        "scheduled_tasks": {
            "enabled": True, "preset": "evening", "hour": 20, "minute": 30,
            "scrape": True, "curate": True, "distribute": True, "notify": True
        },
        "sec_filings": {},
        "macro_indicators": [],
        "discord_channels": [],
        "substack_newsletters": [],
        "wechat_accounts": [],
        "hacker_news": [],
        "reddit_subreddits": [],
        "arxiv_categories": [],
        "rss_subscriptions": [],
        "websites": [],
        "bloggers": []
    }

def save_sources(data):
    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    if os.path.exists(HTML_FILE):
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Web Admin HTML not found</h1>"

@app.get("/api/sources")
async def api_get_sources():
    return load_sources()

@app.post("/api/sources")
async def api_save_sources(request: Request):
    data = await request.json()
    save_sources(data)
    return {"status": "ok", "message": "配置已成功保存！"}

@app.get("/api/config/export")
async def api_export_config():
    data = load_sources()
    content = json.dumps(data, ensure_ascii=False, indent=2)
    today = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"agentfeed-config-{today}.json"
    return Response(
        content=content.encode("utf-8"),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.post("/api/config/save-to-downloads")
async def api_save_to_downloads():
    """Save current configuration directly to ~/Downloads/agentfeed-config-YYYY-MM-DD.json"""
    try:
        downloads_dir = os.path.expanduser("~/Downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        target_file = os.path.join(downloads_dir, f"agentfeed-config-{today_str}.json")
        data = load_sources()
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"success": True, "file_path": target_file, "file_name": os.path.basename(target_file)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/config/import")
async def api_import_config(request: Request):
    try:
        payload = await request.json()
        imported_data = payload.get("config") if isinstance(payload, dict) and "config" in payload else payload
        mode = payload.get("mode", "overwrite") if isinstance(payload, dict) else "overwrite"
        
        if not isinstance(imported_data, dict):
            return JSONResponse(status_code=400, content={"status": "error", "message": "配置文件格式错误，必须是合法的 JSON 对象！"})
        
        if mode == "merge":
            current_data = load_sources()
            for key, val in imported_data.items():
                if isinstance(val, list) and key in current_data and isinstance(current_data[key], list):
                    existing_keys = {item.get("id") or item.get("url") or item.get("symbol") or item.get("name") or item.get("handle") for item in current_data[key] if isinstance(item, dict)}
                    for item in val:
                        item_key = item.get("id") or item.get("url") or item.get("symbol") or item.get("name") or item.get("handle") if isinstance(item, dict) else None
                        if not item_key or item_key not in existing_keys:
                            current_data[key].append(item)
                elif isinstance(val, dict) and key in current_data and isinstance(current_data[key], dict):
                    current_data[key].update(val)
                else:
                    current_data[key] = val
            save_sources(current_data)
            return {"status": "ok", "message": "配置已成功增量合并！", "sources": current_data}
        else:
            save_sources(imported_data)
            return {"status": "ok", "message": "新设备配置已成功全量导入并生效！", "sources": imported_data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"导入失败: {str(e)}"})

@app.get("/api/rsshub-ping")
async def api_rsshub_ping():
    sources = load_sources()
    instances = sources.get("rsshub_instances", {})
    results = {}
    for name, url in instances.items():
        if url:
            results[name] = test_rsshub_latency(url)
    return results

@app.post("/api/test-feed")
async def api_test_feed(request: Request):
    data = await request.json()
    route = data.get("route", "")
    custom_url = data.get("custom_rsshub_url", "")
    result = fetch_single_feed_preview(route, custom_url)
    return result

@app.post("/api/test-sec")
async def api_test_sec(request: Request):
    data = await request.json()
    ticker = data.get("ticker", "NVDA")
    forms = data.get("target_forms", ["8-K", "10-Q", "4", "13F-HR"])
    filings = fetch_sec_filings_for_ticker(ticker, target_forms=forms, limit=3)
    return {
        "success": len(filings) > 0,
        "ticker": ticker.upper(),
        "filings": filings,
        "error": "未查找到相关申报或 CIK 解析失败" if not filings else None
    }

@app.get("/api/macro-quotes")
async def api_macro_quotes():
    sources = load_sources()
    macro_list = sources.get("macro_indicators", [])
    quotes = fetch_macro_indicators(macro_list)
    return quotes

@app.post("/api/test-discord")
async def api_test_discord(request: Request):
    data = await request.json()
    res = fetch_single_discord_preview(data)
    return res

@app.post("/api/test-substack")
async def api_test_substack(request: Request):
    data = await request.json()
    handle = data.get("handle", "")
    articles = fetch_substack_feed(handle, limit=3)
    return {
        "success": len(articles) > 0,
        "handle": handle,
        "articles": articles,
        "error": "未能拉取到专栏文章，请检查 Handle 或链接是否正确" if not articles else None
    }

@app.post("/api/test-hn")
async def api_test_hn():
    res = fetch_single_hn_preview()
    return res

@app.post("/api/test-reddit")
async def api_test_reddit(request: Request):
    data = await request.json()
    subreddit = data.get("subreddit", "LocalLLaMA")
    res = fetch_single_reddit_preview(subreddit)
    return res

@app.post("/api/test-arxiv")
async def api_test_arxiv(request: Request):
    data = await request.json()
    category = data.get("category", "trending")
    res = fetch_single_arxiv_preview(category)
    return res

# ========== Curation & Distribution Endpoints ==========

@app.post("/api/test-llm")
async def api_test_llm(request: Request):
    data = await request.json()
    test_news = [
        {"source": "路透社", "title": "英伟达与台积电扩大先进封装CoWoS产能合作", "summary": "为满足全球 Blackwell 架构 AI 芯片的强劲需求，双方计划进一步提升晶圆代工吞吐量。"},
        {"source": "华尔街日报", "title": "美联储官员示意通胀回落趋势明朗，降息路径渐进展开", "summary": "多位理事表示劳动力市场正在恢复供需平衡，货币政策将逐步回归中性区间。"},
        {"source": "Bloomberg", "title": "NVIDIA orders boost TSMC advanced packaging ramp", "summary": "TSMC accelerates CoWoS expansion as AI accelerator demand remains unprecedented."}
    ]
    curated = curate_daily_intel(
        raw_items=test_news,
        macro_indicators=[{"name": "美债 10Y", "value": "4.25%", "change": "+0.02%", "status": "up"}],
        sec_filings=[{"ticker": "NVDA", "form": "8-K", "description": "重大产能合作协议", "date": "2026-08-24", "url": "https://sec.gov"}],
        sub_articles=[],
        tg_items=[],
        dc_items=[],
        wx_items=[]
    )
    return {
        "success": True,
        "curated": curated
    }

@app.get("/api/obsidian-vaults")
async def api_get_obsidian_vaults():
    vaults = get_obsidian_vaults()
    return {"vaults": vaults}

@app.post("/api/test-obsidian")
async def api_test_obsidian(request: Request):
    data = await request.json()
    vault = data.get("vault", "Investing")
    folder = data.get("folder", "Daily Intel")
    
    sample_data = {
        "lead_summary": "测试：这是一篇由 Antigravity 生成的 Obsidian 笔记测试。",
        "macro_indicators": [{"name": "美债 10Y", "symbol": "^TNX", "value": "4.25%", "change": "+0.02%", "status": "up"}],
        "sec_filings": [{"ticker": "NVDA", "form": "8-K", "description": "重大战略合同", "date": "2026-08-24", "url": "https://sec.gov"}],
        "categories": {
            "AI算力与前沿科技": [
                {"title": "OpenAI 算力部署提速", "facts": "扩大数据中心电力接入", "impact": "利好半导体与电力基建", "tickers": ["NVDA", "MSFT"], "source": "WSJ", "link": "https://wsj.com"}
            ]
        }
    }
    res = save_note_to_obsidian(sample_data, custom_vault=vault, custom_folder=folder)
    return res

@app.post("/api/test-feishu")
async def api_test_feishu(request: Request):
    data = await request.json()
    webhook = data.get("webhook_url", "")
    sample_data = {
        "lead_summary": "【测试推送】飞书群机器人交互式卡片测试成功！大模型梳理与多渠道分发已就绪。",
        "macro_indicators": [
            {"name": "美债 10Y", "value": "4.25%", "change": "+0.02%"},
            {"name": "黄金现货", "value": "$2,510", "change": "+0.45%"}
        ],
        "sec_filings": [{"ticker": "NVDA", "form": "8-K", "description": "重大战略合作协议"}],
        "categories": {
            "AI算力与前沿科技": [
                {"title": "英伟达与台积电深化先进封装产能", "facts": "满足新一代 Blackwell 架构需求", "link": "https://feed.example.com/"}
            ]
        }
    }
    res = send_feishu_brief(sample_data, custom_webhook=webhook)
    return res

@app.post("/api/test-feishu-doc")
async def api_test_feishu_doc(request: Request):
    data = await request.json()
    sample_data = {
        "lead_summary": "【测试】这是一篇由 AgentFeed 自动化智能简报系统生成的飞书云文档连通性测试。",
        "macro_indicators": [
            {"name": "重点指数", "value": "100.0", "change": "+0.5%"},
            {"name": "核心指标", "value": "4.25", "change": "-0.1%"}
        ],
        "sec_filings": [],
        "categories": {
            "🤖 AI 与前沿科技": [
                {"title": "AgentFeed 全源信息感知与智能简报测试", "facts": "跨渠道免登录采集与大模型提炼成功", "impact": "打通飞书云文档多维分发通道", "tags": ["AI", "Agent", "飞书"], "link": "https://feed.your-domain.com/"}
            ]
        }
    }
    res = create_feishu_doc(sample_data, custom_cfg=data)
    return res

@app.post("/api/test-email")
async def api_test_email(request: Request):
    data = await request.json()
    sample_html = """
    <div style="font-family:sans-serif; max-width:600px; margin:0 auto; padding:20px; border:1px solid #e5e7eb; border-radius:10px;">
      <h2 style="color:#1e3a8a;">📰 AgentFeed 每日全源智能简报（测试邮件）</h2>
      <p style="color:#374151;">这是一封来自 AgentFeed 全源信息感知与智能提炼系统的 SMTP 连通性测试邮件。</p>
      <div style="background:#f0fdf4; border-left:4px solid #16a34a; padding:10px 14px; border-radius:6px; color:#166534; font-weight:bold;">
        ✅ SMTP 邮件分发服务配置成功！
      </div>
    </div>
    """
    res = send_email_brief(sample_html, custom_cfg=data)
    return res

@app.get("/api/icon")
@app.get("/icon.png")
async def api_get_icon():
    if os.path.exists(ICON_FILE):
        return FileResponse(ICON_FILE, media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "icon not found"})

@app.get("/api/history")
async def api_get_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

@app.post("/api/trigger")
async def api_trigger():
    try:
        from run_daily_brief import generate_daily_brief
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        f = io.StringIO()
        with redirect_stdout(f), redirect_stderr(f):
            generate_daily_brief()
        output = f.getvalue()
        return {"status": "success", "output": output}
    except Exception as e:
        return {"status": "error", "output": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9830)
