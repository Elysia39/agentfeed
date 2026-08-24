import requests
import feedparser

UA = "Mozilla/5.0 (compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)"

# Public WeChat aggregator endpoints / RSSHub routes
WECHAT_SAMPLE_ROUTES = [
    {"name": "智东西 (AI算力与硬科技)", "route": "/wechat/mp/msghistory/gh_49a9bbf6292b"},
    {"name": "半导体行业观察", "route": "/wechat/mp/msghistory/gh_23bb0d9e79cf"},
    {"name": "晚点LatePost", "route": "/wechat/mp/msghistory/gh_d80d2fb9aa6f"}
]

def fetch_wechat_articles_via_rsshub(base_url, route, timeout=10):
    url = f"{base_url.rstrip('/')}{route}"
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.text)
            return feed.entries
    except Exception:
        pass
    return None

def fetch_all_wechat_articles(custom_accounts=None):
    all_articles = []
    # If custom accounts provided, fetch those, otherwise default industry channels
    accounts = custom_accounts if custom_accounts else WECHAT_SAMPLE_ROUTES
    
    # Try local RSSHub nodes
    nodes = ["https://rsshub.liumingye.cn", "https://rss-hub-hub-bin.vercel.app"]
    
    for acc in accounts:
        name = acc.get("name", "微信公众号")
        route = acc.get("route", "")
        
        entries = None
        for node in nodes:
            entries = fetch_wechat_articles_via_rsshub(node, route)
            if entries:
                break
        
        if entries:
            for entry in entries[:3]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", ""))[:140] + "..."
                link = entry.get("link", "")
                published = entry.get("published", "")
                if title:
                    all_articles.append({
                        "source": name,
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "published": published
                    })
    return all_articles

if __name__ == "__main__":
    arts = fetch_all_wechat_articles()
    print(f"Fetched {len(arts)} WeChat articles.")
