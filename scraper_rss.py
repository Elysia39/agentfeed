import os
import json
import time
import requests
import feedparser
from config import RSSHUB_CONFIG

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(CURRENT_DIR, "sources.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
BOT_UA = "Mozilla/5.0 (compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)"

# URL to RSSHub Route auto-mapper for common sites
URL_TO_ROUTE_MAP = {
    "news.futunn.com/main": "/futunn/highlights",
    "news.futunn.com": "/futunn/highlights",
    "futunn.com": "/futunn/highlights",
    "36kr.com/newsflashes": "/36kr/newsflashes",
    "36kr.com": "/36kr/newsflashes",
    "wsj.com/news/markets": "/wsj/zh-hans/markets",
    "reuters.com": "/reuters/business/markets/us",
    "huxiu.com/moment": "/huxiu/moment",
    "huxiu.com": "/huxiu/moment"
}

def is_direct_xml_or_rss_url(url_str):
    s = url_str.strip().lower()
    if not (s.startswith("http://") or s.startswith("https://")):
        return False
    # Check if known direct XML/RSS extensions or paths
    if any(ext in s for ext in [".xml", ".rss", ".atom", "/feed", "/rss", "/atom", "feed=", "format=rss", "format=xml"]):
        return True
    return True # All full http/https URLs that aren't mapped are treated as potential direct feeds

def normalize_route_or_url(input_str):
    """
    Intelligently converts a full website URL or partial path into a valid RSSHub route or direct XML URL.
    Example: 'https://news.futunn.com/main' -> '/futunn/highlights'
    Example: 'https://blog.cloudflare.com/rss/' -> 'https://blog.cloudflare.com/rss/'
    """
    s = input_str.strip()
    if not s:
        return s
    
    # Check if known website URL in map
    for domain_pattern, mapped_route in URL_TO_ROUTE_MAP.items():
        if domain_pattern in s:
            return mapped_route

    # If it's a direct XML/RSS link (or any full URL)
    if s.startswith("http://") or s.startswith("https://"):
        return s

    # Ensure starts with /
    if not s.startswith("/"):
        s = "/" + s
    return s

def load_sources_data():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def test_rsshub_latency(url):
    """Pings an RSSHub node and returns latency in milliseconds."""
    t0 = time.time()
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=5)
        dt = int((time.time() - t0) * 1000)
        return {"status": resp.status_code, "latency_ms": dt, "ok": resp.status_code in [200, 403]}
    except Exception as e:
        return {"status": "error", "error": str(e), "ok": False}

def fetch_direct_xml_feed(url, timeout=8):
    """Directly fetches and parses a raw XML/RSS/Atom URL without RSSHub."""
    for user_agent in [UA, BOT_UA]:
        try:
            resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
            if resp.status_code == 200 and resp.text:
                feed = feedparser.parse(resp.text)
                if feed.entries:
                    return feed.entries
        except Exception as e:
            pass
    return None

def fetch_feed_from_node(base_url, route, timeout=10):
    norm_route = normalize_route_or_url(route)
    
    # If it's a direct standalone XML / RSS URL
    if norm_route.startswith("http://") or norm_route.startswith("https://"):
        return fetch_direct_xml_feed(norm_route, timeout=timeout)
        
    url = f"{base_url.rstrip('/')}{norm_route}"
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        if resp.status_code == 200 and resp.text:
            feed = feedparser.parse(resp.text)
            if feed.entries:
                return feed.entries
    except Exception as e:
        print(f"⚠️ Failed fetching {url}: {e}")
    return None

def fetch_single_feed_preview(route, custom_url=""):
    """Fetches a single feed for instant UI testing preview."""
    data = load_sources_data()
    instances = data.get("rsshub_instances", {})
    norm_route = normalize_route_or_url(route)
    
    # 1. Direct XML / RSS URL handling
    if norm_route.startswith("http://") or norm_route.startswith("https://"):
        entries = fetch_direct_xml_feed(norm_route, timeout=8)
        if entries:
            return {
                "success": True,
                "node_used": "⚡ 原生 XML/RSS 直连",
                "items": [
                    {
                        "title": e.get("title", ""),
                        "summary": e.get("summary", e.get("description", ""))[:120] + "...",
                        "link": e.get("link", ""),
                        "published": e.get("published", "")
                    }
                    for e in entries[:3]
                ]
            }

    # 2. RSSHub routes
    nodes = []
    if custom_url and custom_url.strip():
        nodes.append(custom_url.strip())
    
    nodes.append(instances.get("primary", RSSHUB_CONFIG["primary"]))
    nodes.append(instances.get("backup", RSSHUB_CONFIG["backup"]))
    nodes.append(instances.get("official", "https://rsshub.app"))

    for node in nodes:
        entries = fetch_feed_from_node(node, norm_route, timeout=8)
        if entries:
            return {
                "success": True,
                "node_used": f"{node}{norm_route}",
                "items": [
                    {
                        "title": e.get("title", ""),
                        "summary": e.get("summary", e.get("description", ""))[:120] + "...",
                        "link": e.get("link", ""),
                        "published": e.get("published", "")
                    }
                    for e in entries[:3]
                ]
            }
            
    return {"success": False, "error": f"无法拉取有效内容。支持输入 XML 订阅直链（如 https://site.com/feed.xml）或 RSSHub 路由（如 /wsj/zh-hans/markets）。"}

def fetch_all_rss_items():
    all_items = []
    data = load_sources_data()
    instances = data.get("rsshub_instances", {})
    primary_node = instances.get("primary", RSSHUB_CONFIG["primary"])
    backup_node = instances.get("backup", RSSHUB_CONFIG["backup"])
    
    subscriptions = data.get("rss_subscriptions", [])
    
    for sub in subscriptions:
        if not sub.get("enabled", True):
            continue
        
        route = sub.get("route", "")
        norm_route = normalize_route_or_url(route)
        custom_node = sub.get("custom_rsshub_url", "").strip()
        sub_name = sub.get("name", "RSS")

        entries = None
        used_node = None

        # If it's a direct standalone XML / RSS URL, fetch directly
        if norm_route.startswith("http://") or norm_route.startswith("https://"):
            entries = fetch_direct_xml_feed(norm_route)
            if entries:
                used_node = "Direct XML"
                print(f"✅ Fetched {len(entries)} items for [{sub_name}] directly from XML URL: {norm_route}")

        # If not direct or direct failed, fallback to RSSHub candidate nodes
        if not entries:
            candidate_nodes = []
            if custom_node:
                candidate_nodes.append(custom_node)
            candidate_nodes.extend([primary_node, backup_node])

            for node in candidate_nodes:
                entries = fetch_feed_from_node(node, norm_route)
                if entries:
                    used_node = node
                    print(f"✅ Fetched {len(entries)} items for [{sub_name}] from {node}{norm_route}")
                    break
        
        if entries:
            for entry in entries[:8]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                link = entry.get("link", "")
                published = entry.get("published", "")
                if title:
                    all_items.append({
                        "source": sub_name,
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "published": published
                    })
    return all_items

if __name__ == "__main__":
    test_xml = fetch_single_feed_preview("https://hnrss.org/frontpage")
    print("Direct XML test result:", test_xml)
