import os
import json
import datetime
import html
from config import R2_CONFIG

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(CURRENT_DIR, "feed_history.json")

MAGAZINE_HTML_STYLE = """
<style>
  .intel-card {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1f2937;
    line-height: 1.6;
    margin-bottom: 24px;
    background: #ffffff;
  }
  .lead-box {
    background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%);
    border-left: 4px solid #0284c7;
    padding: 14px 18px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 15px;
    color: #0c4a6e;
  }
  .macro-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 8px;
    margin-bottom: 18px;
  }
  .macro-item {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 10px;
    text-align: center;
  }
  .macro-name { font-size: 11px; color: #64748b; margin-bottom: 2px; }
  .macro-val { font-size: 14px; font-weight: 700; color: #0f172a; }
  .macro-chg-up { font-size: 11px; color: #dc2626; font-weight: 600; }
  .macro-chg-down { font-size: 11px; color: #16a34a; font-weight: 600; }
  .section-title {
    font-size: 16px;
    font-weight: 700;
    margin: 22px 0 12px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #e5e7eb;
    color: #111827;
    display: flex;
    align-items: center;
  }
  .news-item {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
  }
  .tag {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 700;
  }
  .tag-sec { background: #fef3c7; color: #b45309; }
  .tag-tg { background: #e0e7ff; color: #4338ca; }
  .tag-dc { background: #ede9fe; color: #6d28d9; }
  .tag-sub { background: #ffedd5; color: #c2410c; }
  .tag-wx { background: #dcfce7; color: #15803d; }
  .tag-watchlist { background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; }
  .tag-cat { background: #e0f2fe; color: #0369a1; }
  .quote-box {
    background: #f8fafc;
    border-left: 3px solid #64748b;
    padding: 10px 14px;
    border-radius: 4px;
    margin: 8px 0;
    font-style: italic;
    color: #334155;
  }
  .source-link {
    display: inline-block;
    margin-top: 6px;
    font-size: 12px;
    color: #2563eb;
    text-decoration: none;
  }
</style>
"""

def highlight_keywords(text, watchlist):
    escaped = html.escape(str(text))
    for kw in watchlist:
        if kw in escaped:
            escaped = escaped.replace(kw, f"<strong style='color:#dc2626; background:#fee2e2; padding:0 2px; border-radius:2px;'>{kw}</strong>")
    return escaped

def render_brief_html(lead_summary, macro_indicators, sec_filings, tg_messages, dc_messages, sub_articles, wx_articles, categorized_news, x_insights, market_news, watchlist=None):
    if watchlist is None:
        watchlist = []
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    content = f"{MAGAZINE_HTML_STYLE}\n<div class=\"intel-card\">\n"
    
    # 1. Lead Box
    content += f"""  <div class="lead-box">
    <strong>📌 今日核心速览：</strong> {highlight_keywords(lead_summary, watchlist)}
  </div>\n"""

    # 2. Macro Indicators Dashboard Bar
    if macro_indicators:
        content += "  <div class=\"macro-grid\">\n"
        for m in macro_indicators:
            chg_cls = "macro-chg-up" if m.get("status") == "up" else "macro-chg-down"
            content += f"""    <div class="macro-item">
      <div class="macro-name">{html.escape(m.get('name', ''))}</div>
      <div class="macro-val">{m.get('value', '')}</div>
      <div class="{chg_cls}">{m.get('change', '')}</div>
    </div>\n"""
        content += "  </div>\n"

    # 3. SEC EDGAR Filings
    if sec_filings:
        content += "  <div class=\"section-title\">🏛️ SEC 官方重大披露 & 高管申报 (8-K / 13-F / Form 4)</div>\n"
        for sf in sec_filings:
            content += f"""  <div class="news-item">
    <span class="tag tag-sec">SEC {sf.get('form', '')}</span>
    <span style="font-weight:700; margin-left:6px; color:#111827;">[{sf.get('ticker', '')}]</span>
    <span style="font-size:12px; color:#6b7280; margin-left:6px;">{sf.get('date', '')}</span>
    <div style="font-size:13px; color:#374151; margin-top:4px;">{highlight_keywords(sf.get('description', ''), watchlist)}</div>
    <a class="source-link" href="{sf.get('url', '')}" target="_blank">📄 查看 SEC 原生披露文件 ↗</a>
  </div>\n"""

    # 4. Substack Deep Dives
    if sub_articles:
        content += "  <div class=\"section-title\">📚 Substack 顶级独立投研与行业专栏</div>\n"
        for sub in sub_articles:
            content += f"""  <div class="news-item">
    <span class="tag tag-sub">Substack · {html.escape(sub.get('newsletter', ''))}</span>
    <h4 style="margin:4px 0; font-size:14px; color:#111827;">{highlight_keywords(sub.get('title', ''), watchlist)}</h4>
    <p style="margin:0; font-size:13px; color:#4b5563;">{highlight_keywords(sub.get('summary', ''), watchlist)}</p>
    {f'<a class="source-link" href="{sub["link"]}" target="_blank">🔗 阅读深度研报 ↗</a>' if sub.get('link') else ''}
  </div>\n"""

    # 5. Telegram Intelligence
    if tg_messages:
        content += "  <div class=\"section-title\">✈️ Telegram 一线快讯与突发</div>\n"
        for tg in tg_messages:
            content += f"""  <div class="news-item">
    <span class="tag tag-tg">{html.escape(tg.get('channel', 'TG'))}</span>
    <div style="font-size:13px; color:#1f2937; margin-top:4px; white-space:pre-wrap;">{highlight_keywords(tg.get('text', '')[:280], watchlist)}</div>
    <a class="source-link" href="{tg.get('link', '')}" target="_blank">🔗 打开频道查看 ↗</a>
  </div>\n"""

    # 6. Discord Communities
    if dc_messages:
        content += "  <div class=\"section-title\">🎮 Discord 官方公告与技术讨论</div>\n"
        for dc in dc_messages:
            content += f"""  <div class="news-item">
    <span class="tag tag-dc">Discord · {html.escape(dc.get('source', ''))}</span>
    <div style="font-size:13px; color:#1f2937; margin-top:4px; white-space:pre-wrap;">{highlight_keywords(dc.get('content', '')[:280], watchlist)}</div>
    {f'<a class="source-link" href="{dc["link"]}" target="_blank">🔗 打开 Discord 社区 ↗</a>' if dc.get('link') else ''}
  </div>\n"""

    # 7. WeChat Deep Articles
    if wx_articles:
        content += "  <div class=\"section-title\">💬 微信公众号深度产业专栏</div>\n"
        for wx in wx_articles:
            content += f"""  <div class="news-item">
    <span class="tag tag-wx">{html.escape(wx.get('source', '微信专栏'))}</span>
    <h4 style="margin:4px 0; font-size:14px; color:#111827;">{highlight_keywords(wx.get('title', ''), watchlist)}</h4>
    <p style="margin:0; font-size:13px; color:#4b5563;">{highlight_keywords(wx.get('summary', ''), watchlist)}</p>
    {f'<a class="source-link" href="{wx["link"]}" target="_blank">🔗 阅读全文 ↗</a>' if wx.get('link') else ''}
  </div>\n"""

    # 8. Categorized News
    for cat_name, items in categorized_news.items():
        if not items:
            continue
        content += f"  <div class=\"section-title\">📰 {html.escape(cat_name)}</div>\n"
        for item in items:
            source = item.get("source", "资讯")
            is_watchlist = any(w.lower() in item.get('title', '').lower() for w in watchlist)
            
            content += f"""  <div class="news-item">
    <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
      <span class="tag tag-cat">{html.escape(source)}</span>
      {f'<span class="tag tag-watchlist">🔥 重点标的</span>' if is_watchlist else ''}
    </div>
    <h4 style="margin:4px 0 4px 0; font-size:14px; color:#111827;">{highlight_keywords(item.get('title', ''), watchlist)}</h4>
    <p style="margin:0; font-size:13px; color:#4b5563;">{highlight_keywords(item.get('summary', ''), watchlist)}</p>
    {f'<a class="source-link" href="{item["link"]}" target="_blank">🔗 阅读原文 ↗</a>' if item.get('link') else ''}
  </div>\n"""

    # 9. X (Twitter) Insights
    if x_insights:
        content += "  <div class=\"section-title\">🔵 博主大V 核心洞察</div>\n"
        for tweet in x_insights:
            author = tweet.get("author", "博主")
            text = tweet.get("text", "")
            content += f"""  <div class="news-item">
    <span class="tag tag-cat">大V 观点</span>
    <span style="font-weight:600; color:#0369a1; margin-left:6px; font-size:13px;">{html.escape(author)}</span>
    <div class="quote-box">“{highlight_keywords(text, watchlist)}”</div>
  </div>\n"""

    # 10. Futu / Market news
    if market_news:
        content += "  <div class=\"section-title\">🟡 盘前异动与市场快讯</div>\n"
        for m in market_news:
            content += f"""  <div class="news-item">
    <span class="tag tag-cat">市场快讯</span>
    <h4 style="margin:4px 0 4px 0; font-size:14px; color:#111827;">{highlight_keywords(m.get('title', ''), watchlist)}</h4>
    {f'<p style="margin:0; font-size:13px; color:#4b5563;">{highlight_keywords(m.get("text", ""), watchlist)}</p>' if m.get('text') and m.get('text') != m.get('title') else ''}
  </div>\n"""

    content += "</div>"
    return content

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Failed saving history: {e}")

def build_rss_and_html(rendered_html_body):
    now = datetime.datetime.now(datetime.timezone.utc)
    local_time = datetime.datetime.now()
    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    today_str = local_time.strftime("%Y-%m-%d")
    time_str = local_time.strftime("%H:%M")
    public_domain = R2_CONFIG["public_domain"].rstrip("/")

    guid_val = f"evening-brief-{today_str}-{int(now.timestamp())}"
    issue_title = f"📅 【晚报内参】{today_str} ({time_str}) 宏观、SEC披露、Substack研报与全球要闻"

    current_item = {
        "title": issue_title,
        "link": f"{public_domain}/archive/{today_str}.html",
        "guid": guid_val,
        "pubDate": pub_date,
        "content": rendered_html_body
    }

    history = load_history()
    history = [item for item in history if item.get("guid") != guid_val]
    history.insert(0, current_item)
    history = history[:15]
    save_history(history)

    items_xml = ""
    for itm in history:
        items_xml += f"""    <item>
      <title>{itm['title']}</title>
      <link>{itm['link']}</link>
      <guid isPermaLink="false">{itm['guid']}</guid>
      <pubDate>{itm['pubDate']}</pubDate>
      <description><![CDATA[{itm['content']}]]></description>
      <content:encoded><![CDATA[{itm['content']}]]></content:encoded>
    </item>\n"""

    feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>AgentFeed · 每日全球宏观与市场晚报内参</title>
    <link>{public_domain}/</link>
    <description>AgentFeed - 专为 AI Agent 打造的全源信息感知、大模型智能梳理与多渠道分发框架</description>
    <language>zh-CN</language>
    <lastBuildDate>{pub_date}</lastBuildDate>
{items_xml}  </channel>
</rss>
"""

    standalone_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgentFeed · 每日晚报内参 - {today_str}</title>
  <style>
    body {{
      background: #f3f4f6;
      margin: 0;
      padding: 24px 16px;
      display: flex;
      justify-content: center;
    }}
    .container {{
      max-width: 720px;
      width: 100%;
      background: #ffffff;
      padding: 24px 32px;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    h1 {{
      font-size: 20px;
      margin-top: 0;
      color: #111827;
      border-bottom: 2px solid #e5e7eb;
      padding-bottom: 12px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>📡 AgentFeed 晚报内参 ({today_str} {time_str})</h1>
    {rendered_html_body}
  </div>
</body>
</html>
"""
    return feed_xml, standalone_html
