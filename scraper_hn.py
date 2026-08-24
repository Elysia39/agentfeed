import requests
import html

def fetch_hacker_news_top(limit=10):
    """
    Fetch top stories from Hacker News using Algolia's open public API (100% zero-login).
    """
    url = f"https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage={limit}"
    headers = {
        "User-Agent": "AgentFeed/1.0 (https://github.com/agentfeed/agentfeed)"
    }
    results = []
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", [])
            for item in hits:
                title = item.get("title") or item.get("story_title") or ""
                link = item.get("url") or f"https://news.ycombinator.com/item?id={item.get('objectID')}"
                points = item.get("points") or 0
                num_comments = item.get("num_comments") or 0
                author = item.get("author") or "unknown"
                hn_item_url = f"https://news.ycombinator.com/item?id={item.get('objectID')}"
                
                results.append({
                    "title": html.unescape(title),
                    "link": link,
                    "hn_discussion": hn_item_url,
                    "points": points,
                    "num_comments": num_comments,
                    "author": author,
                    "source": "Hacker News"
                })
    except Exception as e:
        print(f"⚠️ Failed to fetch Hacker News: {e}")
    return results

def fetch_single_hn_preview():
    items = fetch_hacker_news_top(limit=5)
    return {
        "success": len(items) > 0,
        "items": items,
        "error": "未能拉取到 Hacker News 热门条目" if not items else None
    }

if __name__ == "__main__":
    top = fetch_hacker_news_top(5)
    print(f"Fetched {len(top)} items from HN:")
    for t in top:
        print(f"- [{t['points']} pts] {t['title']} ({t['link']})")
