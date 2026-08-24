import os
import json
import re
import datetime
import subprocess
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
from paths import SOURCES_FILE

def load_llm_config():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                return sdata.get("llm_settings", {
                    "enabled": False,
                    "provider": "openai_compatible", # openai_compatible, openai_responses, google, claude, local_agent
                    "api_key": "",
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                    "temperature": 0.3
                })
        except Exception:
            pass
    return {
        "enabled": False,
        "provider": "openai_compatible",
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "temperature": 0.3
    }

# 1. OpenAI Compatible Protocol (DeepSeek / SiliconFlow / OpenAI / Qwen / Moonshot)
def call_openai_compatible(messages, cfg):
    api_key = cfg.get("api_key", "").strip()
    base_url = cfg.get("base_url", "https://api.deepseek.com/v1").rstrip("/")
    model = cfg.get("model", "deepseek-chat")
    
    if not api_key:
        raise ValueError("LLM API Key 未配置")
        
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": cfg.get("temperature", 0.3),
        "response_format": {"type": "json_object"} if "deepseek" in model or "gpt" in model or "qwen" in model else None
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI 兼容接口错误 ({resp.status_code}): {resp.text}")
        
    res_json = resp.json()
    return res_json["choices"][0]["message"]["content"]

# 2. OpenAI New Responses API Protocol
def call_openai_responses(messages, cfg):
    api_key = cfg.get("api_key", "").strip()
    base_url = cfg.get("base_url", "https://api.openai.com/v1").rstrip("/")
    model = cfg.get("model", "gpt-4o")
    
    if not api_key:
        raise ValueError("OpenAI API Key 未配置")
        
    url = f"{base_url}/responses" if base_url.endswith("/v1") else f"{base_url}/v1/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Pack input text
    input_prompt = "\n\n".join([f"[{m['role'].upper()}]: {m['content']}" for m in messages])
    payload = {
        "model": model,
        "input": input_prompt,
        "temperature": cfg.get("temperature", 0.3)
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        # Fallback to standard chat completions if responses endpoint not supported on target gateway
        return call_openai_compatible(messages, cfg)
        
    res_json = resp.json()
    output_text = res_json.get("output_text", "")
    if not output_text and "output" in res_json:
        output_text = res_json["output"]
    return output_text or json.dumps(res_json)

# 3. Google Gemini API Protocol (gemini-2.5-pro, gemini-2.5-flash, gemini-1.5-pro, gemini-1.5-flash)
def call_google_gemini(messages, cfg):
    api_key = cfg.get("api_key", "").strip()
    model = cfg.get("model", "gemini-2.5-flash").strip()
    if not api_key:
        raise ValueError("Google Gemini API Key 未配置")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Format contents for Gemini API
    system_instruction = ""
    contents = []
    for m in messages:
        if m["role"] == "system":
            system_instruction += m["content"] + "\n"
        else:
            contents.append({
                "role": "user" if m["role"] == "user" else "model",
                "parts": [{"text": m["content"]}]
            })
            
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": cfg.get("temperature", 0.2),
            "responseMimeType": "application/json"
        }
    }
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }
        
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Google Gemini API 错误 ({resp.status_code}): {resp.text}")
        
    res_json = resp.json()
    candidates = res_json.get("candidates", [])
    if candidates and "content" in candidates[0]:
        parts = candidates[0]["content"].get("parts", [])
        if parts and "text" in parts[0]:
            return parts[0]["text"]
    raise RuntimeError(f"Google Gemini 返回结构解析失败: {res_json}")

# 4. Anthropic Claude API Protocol (Claude 3.7 / 3.5 Sonnet & Haiku)
def call_anthropic(messages, cfg):
    api_key = cfg.get("api_key", "").strip()
    model = cfg.get("model", "claude-3-5-haiku-20241022").strip()
    if not api_key:
        raise ValueError("Claude API Key 未配置")
        
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    system_prompt = ""
    user_content = ""
    for m in messages:
        if m["role"] == "system":
            system_prompt += m["content"] + "\n"
        elif m["role"] == "user":
            user_content += m["content"] + "\n"
            
    payload = {
        "model": model,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_content}]
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Anthropic API 错误 ({resp.status_code}): {resp.text}")
    return resp.json()["content"][0]["text"]

# 5. Local Agent CLI Protocol (Antigravity / Codex / ClaudeCode CLI)
def call_local_agent(messages, cfg):
    user_content = ""
    for m in messages:
        user_content += f"[{m['role'].upper()}]: {m['content']}\n"
        
    # Check for local agent CLI (agy / codex / claude)
    import shutil
    agy_bin = shutil.which("agy") or os.path.expanduser("~/.local/bin/agy")
    codex_bin = shutil.which("codex")
    claude_bin = shutil.which("claude")
    
    if agy_bin and os.path.exists(agy_bin):
        try:
            cmd = [agy_bin, "-p", "你是一个专业结构化投资分析助手，请严格以纯 JSON 输出:\n" + user_content[:2000]]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except Exception as e:
            print(f"⚠️ agy CLI 调用未就绪: {e}")
            
    if codex_bin and os.path.exists(codex_bin):
        try:
            cmd = [codex_bin, "exec", user_content[:2000]]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except Exception as e:
            print(f"⚠️ codex CLI 调用未就绪: {e}")

    if claude_bin and os.path.exists(claude_bin):
        try:
            cmd = [claude_bin, "-p", user_content[:2000]]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except Exception as e:
            print(f"⚠️ claude CLI 调用未就绪: {e}")
            
    raise RuntimeError("本地 Agent CLI 未响应，无缝转入本地高性能规则引擎。")

def fallback_rule_curate(raw_items, macro_indicators, sec_filings, sub_articles, tg_items, dc_items, wx_items):
    """
    High-quality local fallback curation if LLM is disabled, offline or using local agent.
    """
    seen_titles = set()
    cleaned_news = []
    
    for item in raw_items:
        t = item.get("title", "").strip()
        norm = "".join(c for c in t if c.isalnum())[:20]
        if norm and norm not in seen_titles:
            seen_titles.add(norm)
            cleaned_news.append(item)
            
    categories = {
        "宏观流动性与大类资产": [],
        "AI算力与前沿科技": [],
        "美股核心公司与财报": [],
        "全球市场与行业要闻": []
    }
    
    for itm in cleaned_news:
        t_low = itm.get("title", "").lower() + " " + itm.get("summary", "").lower()
        if any(w in t_low for w in ["ai", "gpu", "英伟达", "nvda", "tsmc", "台积电", "芯片", "半导体", "模型", "openai", "blackwell"]):
            categories["AI算力与前沿科技"].append(itm)
        elif any(w in t_low for w in ["美联储", "降息", "加息", "通胀", "cpi", "非农", "美债", "美元", "汇率", "fomc"]):
            categories["宏观流动性与大类资产"].append(itm)
        elif any(w in t_low for w in ["财报", "营收", "利润", "sec", "披露", "高管", "减持", "aapl", "msft", "tsla", "meta", "goog"]):
            categories["美股核心公司与财报"].append(itm)
        else:
            categories["全球市场与行业要闻"].append(itm)
            
    lead = "今日宏观利率与汇率窄幅整理，半导体AI产业链维持活跃，重点关注标的最新申报与行业深度研报。"
    
    return {
        "lead_summary": lead,
        "categories": categories,
        "sec_filings": sec_filings[:6],
        "macro_indicators": macro_indicators,
        "substack_articles": sub_articles[:4],
        "telegram_alerts": tg_items[:4],
        "discord_alerts": dc_items[:4],
        "wechat_articles": wx_items[:4]
    }

def curate_daily_intel(raw_items, macro_indicators, sec_filings, sub_articles, tg_items, dc_items, wx_items):
    """
    Main orchestration function for LLM Curation (去重、分类、摘要、买方提炼).
    Supports: OpenAI Compatible, OpenAI Responses, Google Gemini, Anthropic Claude, Local Agent Fallback.
    """
    cfg = load_llm_config()
    provider = cfg.get("provider", "openai_compatible")
    
    if not cfg.get("enabled", False) or (provider != "local_agent" and not cfg.get("api_key", "").strip()):
        print(f"ℹ️ LLM 未配置外置 API Key，默认使用电脑本地 Agent / 高性能规则梳理引擎。")
        return fallback_rule_curate(raw_items, macro_indicators, sec_filings, sub_articles, tg_items, dc_items, wx_items)
        
    print(f"🤖 正在调用大模型 [协议: {provider}, 模型: {cfg.get('model', 'deepseek-chat')}] 对全源数据进行买方级去重、分类与结构化摘要...")
    
    # Pack input context for LLM
    news_input = []
    for idx, item in enumerate(raw_items[:35]):
        news_input.append({
            "id": idx + 1,
            "source": item.get("source", "资讯"),
            "title": item.get("title", ""),
            "summary": item.get("summary", "")[:200],
            "link": item.get("link", "")
        })
        
    system_prompt = """你是一位资深的华尔街买方投资经理与宏观科技策略分析师。
你的任务是将当天采集到的多渠道海量原始资讯进行「买方级专业梳理」：
1. 【去重与合并】：将报道同一事件的多条快讯合并为一条最完整、高密度的信息。
2. 【买方深度摘要】：每条保留的新闻提炼出「核心事实 + 逻辑推演/影响 + 涉及标的Ticker」。
3. 【多维行业分类】：将新闻归入以下分类之一：
   - 宏观流动性与大类资产
   - AI算力与半导体产业链
   - 美股核心公司与财报披露
   - 加密资产与前沿科技
   - 全球商业与行业精选
4. 【生成 Lead 速览】：输出 1-2 句高信息密度的今日大盘与行业核心结论。

你必须严格以合法的 JSON 格式返回，JSON 结构如下：
{
  "lead_summary": "今日核心全局总结（2句话以内）",
  "curated_categories": [
    {
      "category_name": "分类名称",
      "items": [
        {
          "title": "精炼后的标题",
          "facts": "核心事实陈述（50字内）",
          "impact": "对市场/产业的潜在影响分析（50字内）",
          "tickers": ["NVDA", "TSM"],
          "source": "来源媒体",
          "link": "原文链接"
        }
      ]
    }
  ]
}"""

    user_prompt = f"""以下是今日收集到的候选新闻列表（共 {len(news_input)} 条）：
{json.dumps(news_input, ensure_ascii=False, indent=1)}

请进行去重、深度买方摘要与分类，直接输出 JSON 结果："""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        if provider == "google":
            raw_response = call_google_gemini(messages, cfg)
        elif provider == "claude":
            raw_response = call_anthropic(messages, cfg)
        elif provider == "openai_responses":
            raw_response = call_openai_responses(messages, cfg)
        elif provider == "local_agent":
            raw_response = call_local_agent(messages, cfg)
        else: # openai_compatible
            raw_response = call_openai_compatible(messages, cfg)
            
        # Parse JSON
        clean_json = raw_response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        curated_data = json.loads(clean_json)
        
        # Build category map
        cat_map = {}
        for cat in curated_data.get("curated_categories", []):
            cat_name = cat.get("category_name", "精选资讯")
            cat_map[cat_name] = cat.get("items", [])
            
        print("✅ 大模型智能梳理完成！去重并提炼出结构化买方晚报。")
        return {
            "lead_summary": curated_data.get("lead_summary", "今日宏观与全球核心资产平稳。"),
            "categories": cat_map,
            "sec_filings": sec_filings,
            "macro_indicators": macro_indicators,
            "substack_articles": sub_articles,
            "telegram_alerts": tg_items,
            "discord_alerts": dc_items,
            "wechat_articles": wx_items
        }
    except Exception as e:
        print(f"⚠️ LLM 梳理发生异常: {e}，自动降级为本地高性能规则引擎。")
        return fallback_rule_curate(raw_items, macro_indicators, sec_filings, sub_articles, tg_items, dc_items, wx_items)

# ========== Multi-format Converters ==========

def build_obsidian_markdown(curated_result):
    """
    Builds an Obsidian-optimized Markdown note with YAML frontmatter, tags, and [[Wikilinks]].
    """
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    now_str = datetime.datetime.now().strftime("%H:%M")
    
    lead = curated_result.get("lead_summary", "")
    categories = curated_result.get("categories", {})
    sec_filings = curated_result.get("sec_filings", [])
    macro = curated_result.get("macro_indicators", [])
    substack = curated_result.get("substack_articles", [])
    tg = curated_result.get("telegram_alerts", [])
    dc = curated_result.get("discord_alerts", [])
    wx = curated_result.get("wechat_articles", [])

    md = f"""---
date: {today_str}
type: 晚报内参
tags:
  - 每日内参
  - 投研简报
  - 全球宏观
updated: {now_str}
---

# 📰 全球宏观与市场晚报内参 · {today_str}

> [!abstract] 📌 今日核心速览 (Lead Summary)
> {lead}

---

## 📊 全球宏观与大类资产实时看板

| 指标名称 | 代码/标的 | 最新行情 | 当日涨跌 |
| :--- | :--- | :--- | :--- |
"""
    for m in macro:
        sym = m.get("symbol", "")
        name = m.get("name", sym)
        val = m.get("value", "--")
        chg = m.get("change", "--")
        status = m.get("status", "up")
        arrow = "🔺" if status == "up" else "🔻"
        md += f"| **{name}** | `[[{sym}]]` | **{val}** | {arrow} `{chg}` |\n"

    if sec_filings:
        md += "\n---\n\n## 🏛️ SEC EDGAR 官方重大申报与持仓变动\n\n"
        for s in sec_filings:
            ticker = s.get("ticker", "")
            form = s.get("form", "")
            desc = s.get("description", "")
            date = s.get("date", "")
            url = s.get("url", "")
            md += f"- **[[{ticker}]]** `Form {form}` ({date}): {desc} [🔗 SEC 原文]({url})\n"

    for cat_name, items in categories.items():
        if not items:
            continue
        md += f"\n---\n\n## 🔥 {cat_name}\n\n"
        for itm in items:
            title = itm.get("title", "")
            facts = itm.get("facts", itm.get("summary", ""))
            impact = itm.get("impact", "")
            tickers = itm.get("tickers", [])
            source = itm.get("source", "")
            link = itm.get("link", "")
            
            md += f"### {title}\n"
            if source:
                md += f"*来源: {source}*"
                if link:
                    md += f" · [查看原文]({link})"
                md += "\n\n"
            md += f"- **事实陈述**: {facts}\n"
            if impact:
                md += f"- **逻辑推演**: {impact}\n"
            if tickers:
                ticker_links = " ".join([f"[[{t}]]" for t in tickers])
                md += f"- **涉及标的**: {ticker_links}\n"
            md += "\n"

    if substack:
        md += "\n---\n\n## 📚 Substack 顶级独立投研专栏\n\n"
        for sub in substack:
            md += f"- **[{sub.get('title', '')}]({sub.get('link', '')})** — *{sub.get('author', '')} ({sub.get('date', '')})*\n  > {sub.get('summary', '')}\n"

    if tg:
        md += "\n---\n\n## ✈️ Telegram 实时突发快讯\n\n"
        for t in tg:
            md += f"- **[{t.get('channel', 'TG')}]** {t.get('content', '')}\n"

    if dc:
        md += "\n---\n\n## 🎮 Discord 社区精选动态\n\n"
        for d in dc:
            md += f"- **[{d.get('author', d.get('channel', 'Discord'))}]** {d.get('content', '')}\n"

    if wx:
        md += "\n---\n\n## 💬 微信公众号深度纪要\n\n"
        for w in wx:
            md += f"- **[{w.get('title', '')}]({w.get('link', '')})**\n  > {w.get('summary', '')}\n"

    return md
