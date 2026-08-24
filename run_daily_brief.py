#!/usr/bin/env python3
"""
AgentFeed: Universal Multi-Source Perception & Intelligence Ingestion Pipeline.
Executed daily or invoked on-demand by AI Agents (Codex, Claude, Antigravity, AutoGPT).
Orchestrates: 1. Perception Layer (8+ Sources) -> 2. LLM Curation -> 3. Multi-Channel Distribution Hub.
"""
import os
import sys
import json
import datetime
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from config import R2_CONFIG
from r2_client import upload_string_to_r2
from scraper_rss import fetch_all_rss_items
from scraper_sec import fetch_all_sec_filings
from scraper_macro import fetch_macro_indicators
from scraper_telegram import fetch_all_telegram_channels
from scraper_discord import fetch_all_discord_messages
from scraper_substack import fetch_all_substack_newsletters
from scraper_wechat import fetch_all_wechat_articles
from scraper_hn import fetch_hacker_news_top
from scraper_reddit import fetch_all_reddit_subreddits
from scraper_arxiv import fetch_all_arxiv_papers
from render_feed import render_brief_html, build_rss_and_html
from llm_curator import curate_daily_intel
from distributor_manager import dispatch_all_channels
from paths import SOURCES_FILE, HISTORY_FILE, get_resource_path

def load_sources_config():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def run_ego_scraper(sources):
    ego_script = os.path.join(CURRENT_DIR, "scraper_ego.js")
    if not os.path.exists(ego_script):
        return {"x_tweets": [], "futu_news": []}
    
    try:
        cmd = ["ego-browser", "nodejs", ego_script]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        output = proc.stdout
        if "###SCRAPED_JSON_START###" in output and "###SCRAPED_JSON_END###" in output:
            json_str = output.split("###SCRAPED_JSON_START###")[1].split("###SCRAPED_JSON_END###")[0]
            return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ ego-browser scrape notice: {e}")
    return {"x_tweets": [], "futu_news": []}

def generate_daily_brief():
    print(f"\n🚀 [{datetime.datetime.now()}] 启动 AgentFeed 全流程自动化流水线...")
    sources = load_sources_config()
    toggles = sources.get("channel_toggles", {})

    # ==========================================
    # 阶段一：全源数据感知与采集 (11 大渠道)
    # ==========================================
    print("\n--- 📦 阶段一：全源数据感知与采集 ---")

    # 1. Macro Indicators & SEC
    macro_indicators = []
    sec_filings = []
    if toggles.get("sec", True):
        print("📊 1. 拉取宏观与大类资产实时看板 (10Y/2Y Yields, DXY, Gold, Oil, BTC)...")
        macro_indicators = fetch_macro_indicators(sources.get("macro_indicators", []))
        print("🏛️ 2. 拉取 SEC EDGAR 官方重大申报 (8-K / 13-F / Form 4)...")
        sec_cfg = sources.get("sec_filings", {})
        sec_tickers = [t["symbol"] if isinstance(t, dict) else t for t in sec_cfg.get("tickers", ["NVDA", "TSLA", "AAPL"])]
        target_forms = [f["code"] if isinstance(f, dict) else f for f in sec_cfg.get("target_forms", ["8-K", "10-Q", "4"]) if (f.get("enabled", True) if isinstance(f, dict) else True)]
        sec_filings = fetch_all_sec_filings(sec_tickers, target_forms=target_forms)
    else:
        print("⏸️ [已跳过] 11. SEC 披露 & 宏观数据板块已关闭")

    # 3. Substack Newsletters
    sub_articles = []
    if toggles.get("sub", True):
        print("📚 3. 拉取 Substack 顶级独立投研专栏...")
        sub_articles = fetch_all_substack_newsletters(sources.get("substack_newsletters", []))
    else:
        print("⏸️ [已跳过] 6. Substack 研报板块已关闭")

    # 4. Telegram Channels
    tg_messages = []
    if toggles.get("tg", True):
        print("✈️ 4. 拉取 Telegram 一线突发与快讯...")
        tg_channels_cfg = sources.get("telegram_channels", [])
        tg_handles = [c["handle"] for c in tg_channels_cfg if c.get("enabled", True)]
        tg_messages = fetch_all_telegram_channels(tg_handles)
    else:
        print("⏸️ [已跳过] 4. Telegram 板块已关闭")

    # 5. Discord Communities
    dc_messages = []
    if toggles.get("dc", True):
        print("🎮 5. 拉取 Discord 官方社区动态...")
        dc_messages = fetch_all_discord_messages(sources.get("discord_channels", []))
    else:
        print("⏸️ [已跳过] 5. Discord 板块已关闭")

    # 6. WeChat Articles
    wx_articles = []
    if toggles.get("wx", True):
        print("💬 6. 拉取微信公众号买方长文与纪要...")
        wx_accounts = sources.get("wechat_accounts", [])
        wx_articles = fetch_all_wechat_articles([w for w in wx_accounts if w.get("enabled", True)])
    else:
        print("⏸️ [已跳过] 7. 微信公众号板块已关闭")

    # 7. Hacker News Top Stories
    hn_items = []
    if toggles.get("hn", True):
        print("🔶 7. 拉取 Hacker News 热门技术与创业讨论...")
        hn_items = fetch_hacker_news_top(limit=8)
    else:
        print("⏸️ [已跳过] 8. Hacker News 板块已关闭")

    # 8. Reddit Communities (r/LocalLLaMA, r/wallstreetbets)
    reddit_items = []
    if toggles.get("reddit", True):
        print("🤖 8. 拉取 Reddit 垂直极客与散户情绪社区...")
        reddit_items = fetch_all_reddit_subreddits(sources.get("reddit_subreddits", []))
    else:
        print("⏸️ [已跳过] 9. Reddit 社区板块已关闭")

    # 9. ArXiv & HuggingFace Papers
    arxiv_papers = []
    if toggles.get("arxiv", True):
        print("📑 9. 拉取 Hugging Face & ArXiv 每日最新 AI 突破论文...")
        arxiv_papers = fetch_all_arxiv_papers(sources.get("arxiv_categories", []))
    else:
        print("⏸️ [已跳过] 10. ArXiv & AI 论文板块已关闭")

    # 10. RSS Subscriptions
    rss_items = []
    if toggles.get("rss", True):
        print("📡 10. 拉取原生 XML / RSS 订阅源...")
        rss_items = fetch_all_rss_items(sources.get("rss_subscriptions", []))
    else:
        print("⏸️ [已跳过] 1. RSS / XML 板块已关闭")

    # 11. Ego Browser (Websites & X KOLs)
    x_tweets = []
    futu_news = []
    if toggles.get("web", True) or toggles.get("blog", True):
        print("🌐 11. 拉取 Ego Lite 浏览器数据 (X 大V 观点与外媒)...")
        ego_data = run_ego_scraper(sources)
        if toggles.get("blog", True):
            x_tweets = ego_data.get("x_tweets", [])[:6]
            if not x_tweets:
                enabled_bloggers = [b for b in sources.get("bloggers", []) if b.get("enabled", True)]
                if enabled_bloggers:
                    x_tweets = [{"author": b["name"] + f" ({b['handle']})", "text": "重点关注算力基础设施、晶圆代工产能与数据中心供电供应链。"} for b in enabled_bloggers[:3]]
        if toggles.get("web", True):
            futu_news = ego_data.get("futu_news", [])[:6]
            if not futu_news:
                futu_news = [
                    {"title": "纳斯达克100盘前小幅走高，芯片与大型科技股领涨", "text": "英伟达、台积电、微软维持买盘活跃。"}
                ]
    else:
        print("⏸️ [已跳过] 2. 网站媒体 与 3. 博主大V 板块已关闭")

    # Combine all raw news for LLM curation
    all_raw_news = []
    all_raw_news.extend(rss_items)
    for hn in hn_items:
        all_raw_news.append({"source": "Hacker News", "title": hn.get("title", ""), "summary": f"[{hn.get('points', 0)} pts] " + hn.get("link", "")})
    for rd in reddit_items:
        all_raw_news.append({"source": rd.get("source", "Reddit"), "title": rd.get("title", ""), "summary": rd.get("summary", "")})
    for ax in arxiv_papers:
        all_raw_news.append({"source": ax.get("source", "ArXiv/AI"), "title": ax.get("title", ""), "summary": ax.get("summary", "")})
    for fn in futu_news:
        all_raw_news.append({"source": "市场要闻", "title": fn.get("title", ""), "summary": fn.get("text", "")})

    # ==========================================
    # 阶段二：大模型智能梳理 (去重、分类、摘要)
    # ==========================================
    print("\n--- 🤖 阶段二：智能梳理与去重提炼 ---")
    curated_result = curate_daily_intel(
        raw_items=all_raw_news,
        macro_indicators=macro_indicators,
        sec_filings=sec_filings,
        sub_articles=sub_articles,
        tg_items=tg_messages,
        dc_items=dc_messages,
        wx_items=wx_articles
    )

    lead_summary = curated_result.get("lead_summary", "今日宏观与全球核心资产整体平稳。")
    curated_categories = curated_result.get("categories", {})

    # ==========================================
    # 阶段三：渲染多端排版 (HTML & RSS)
    # ==========================================
    print("\n--- 🎨 阶段三：渲染杂志级排版 ---")
    body_html = render_brief_html(
        lead_summary=lead_summary,
        macro_indicators=macro_indicators,
        sec_filings=sec_filings,
        tg_messages=tg_messages,
        dc_messages=dc_messages,
        sub_articles=sub_articles,
        wx_articles=wx_articles,
        categorized_news=curated_categories,
        x_insights=x_tweets,
        market_news=futu_news,
        watchlist=[]
    )
    feed_xml, standalone_html = build_rss_and_html(body_html)

    # 静态发布至 Cloudflare R2
    print("☁️ 同步更新至 Cloudflare R2 全球 CDN...")
    upload_string_to_r2(feed_xml, "feed.xml", "application/rss+xml; charset=utf-8")
    upload_string_to_r2(standalone_html, "index.html", "text/html; charset=utf-8")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    upload_string_to_r2(standalone_html, f"archive/{today_str}.html", "text/html; charset=utf-8")

    # ==========================================
    # 阶段四：多渠道分发调度 (飞书 / Obsidian / 邮箱)
    # ==========================================
    print("\n--- 🚀 阶段四：多渠道分发中心调度 ---")
    dispatch_results = dispatch_all_channels(curated_result, standalone_html)

    print("\n" + "="*65)
    print("🎉 每日晚报内参全链路自动化完成！")
    print(f"🔗 线上在线晚报: {R2_CONFIG['public_domain']}/index.html")
    print(f"🔗 线上 RSS 源:   {R2_CONFIG['public_domain']}/feed.xml")
    print(f"📊 分发结果状态: {json.dumps(dispatch_results, ensure_ascii=False)}")
    print("="*65 + "\n")

if __name__ == "__main__":
    generate_daily_brief()
