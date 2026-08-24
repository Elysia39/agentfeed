import os
import json
import requests
import feedparser
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
from paths import SOURCES_FILE
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def clean_html_summary(raw_html):
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = ' '.join(clean.split())
    return clean[:350]

def fetch_substack_via_jina(handle_or_url, limit=3):
    clean = handle_or_url.strip()
    if clean.startswith("http://") or clean.startswith("https://"):
        base_url = clean.replace("/feed", "")
    else:
        base_url = f"https://{clean}.substack.com"
    
    jina_url = f"https://r.jina.ai/{base_url}"
    try:
        resp = requests.get(jina_url, headers={"User-Agent": UA}, timeout=10)
        if resp.status_code == 200 and resp.text:
            text = resp.text
            matches = re.findall(r'\[([^\]\n]+)\]\((https://[^\)]+/p/[^\)]+)\)', text)
            results = []
            seen = set()
            for title, url in matches:
                title_clean = title.strip()
                if url not in seen and len(title_clean) > 6 and not title_clean.startswith("Image") and not title_clean.startswith("http"):
                    seen.add(url)
                    results.append({
                        "title": title_clean,
                        "link": url.strip(),
                        "author": clean,
                        "date": "最新深度专栏",
                        "summary": f"深度长文与宏观研报：{title_clean}"
                    })
                    if len(results) >= limit:
                        break
            if results:
                return results
    except Exception as e:
        print(f"⚠️ Jina fallback error: {e}")
    return []

def fetch_substack_feed(name_or_url, limit=3):
    clean = name_or_url.strip()
    if clean.startswith("http://") or clean.startswith("https://"):
        if clean.endswith("/"):
            clean = clean[:-1]
        feed_url = clean if clean.endswith("/feed") else f"{clean}/feed"
    else:
        feed_url = f"https://{clean}.substack.com/feed"

    try:
        resp = requests.get(feed_url, headers={"User-Agent": UA}, timeout=6)
        if resp.status_code == 200 and "<rss" in resp.text:
            feed = feedparser.parse(resp.text)
            results = []
            for entry in feed.entries[:limit]:
                title = entry.get("title", "未命名文章")
                link = entry.get("link", "")
                pub_date = entry.get("published", "")
                author = entry.get("author", clean)
                summary = clean_html_summary(entry.get("summary", entry.get("description", "")))
                
                results.append({
                    "title": title,
                    "link": link,
                    "author": author,
                    "date": pub_date,
                    "summary": summary
                })
            if results:
                return results
    except Exception:
        pass

    return fetch_substack_via_jina(name_or_url, limit=limit)

def fetch_all_substack_newsletters():
    all_articles = []
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                newsletters = sdata.get("substack_newsletters", [])
        except Exception:
            newsletters = []
    else:
        newsletters = []

    for item in newsletters:
        if not item.get("enabled", True):
            continue
        
        name = item.get("name", "")
        handle = item.get("handle", item.get("url", ""))
        articles = fetch_substack_feed(handle, limit=2)
        
        for art in articles:
            all_articles.append({
                "newsletter": name or art.get("author", "Substack"),
                "title": art.get("title", ""),
                "summary": art.get("summary", ""),
                "link": art.get("link", ""),
                "date": art.get("date", "")
            })
            
    return all_articles

if __name__ == "__main__":
    print("Testing SemiAnalysis Substack pull...")
    res = fetch_substack_feed("https://www.semianalysis.com/feed", limit=2)
    for r in res:
        print(f"  [{r['author']}] {r['title']} -> {r['link']}")

    print("\nTesting The Macro Compass Substack pull...")
    res2 = fetch_substack_feed("themacrocompass", limit=2)
    for r in res2:
        print(f"  [{r['author']}] {r['title']} -> {r['link']}")
