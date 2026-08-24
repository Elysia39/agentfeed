import requests
import html
import xml.etree.ElementTree as ET
import re

def clean_html(raw_html):
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return html.unescape(cleantext).strip()

def fetch_reddit_subreddit_posts(subreddit="LocalLLaMA", sort="hot", limit=5):
    """
    Fetch posts from a Subreddit using Reddit's open .rss endpoint with SearchBot UA fallback.
    """
    clean_sub = subreddit.replace("r/", "").replace("/", "").strip()
    url = f"https://www.reddit.com/r/{clean_sub}/.rss"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)"
    }
    results = []
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            atom_ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", atom_ns)
            for entry in entries[:limit]:
                title_elem = entry.find("atom:title", atom_ns)
                title = title_elem.text.strip() if title_elem is not None else ""
                
                link_elem = entry.find("atom:link", atom_ns)
                link = link_elem.get("href", "") if link_elem is not None else ""
                
                content_elem = entry.find("atom:content", atom_ns)
                raw_content = content_elem.text if content_elem is not None else ""
                summary = clean_html(raw_content)[:220]
                if len(summary) > 220:
                    summary += "..."
                
                author_elem = entry.find("atom:author/atom:name", atom_ns)
                author = author_elem.text if author_elem is not None else "u/anonymous"

                results.append({
                    "title": html.unescape(title),
                    "summary": summary if summary else title,
                    "link": link,
                    "author": author,
                    "subreddit": f"r/{clean_sub}",
                    "source": f"Reddit (r/{clean_sub})"
                })
    except Exception as e:
        print(f"⚠️ Failed to fetch Reddit r/{clean_sub}: {e}")
    return results

def fetch_all_reddit_subreddits(subreddits_config):
    all_posts = []
    for item in subreddits_config:
        if not item.get("enabled", True):
            continue
        sub = item.get("subreddit") or item.get("name")
        limit = item.get("limit", 4)
        posts = fetch_reddit_subreddit_posts(sub, limit=limit)
        all_posts.extend(posts)
    return all_posts

def fetch_single_reddit_preview(subreddit="LocalLLaMA"):
    posts = fetch_reddit_subreddit_posts(subreddit, limit=4)
    return {
        "success": len(posts) > 0,
        "subreddit": subreddit,
        "posts": posts,
        "error": f"未能从 r/{subreddit} 拉取到帖子，请检查名称是否正确" if not posts else None
    }

if __name__ == "__main__":
    posts = fetch_reddit_subreddit_posts("LocalLLaMA", limit=3)
    print(f"Fetched {len(posts)} posts from r/LocalLLaMA:")
    for p in posts:
        print(f"- {p['title']} ({p['link']})")
