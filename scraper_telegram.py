import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)"

def fetch_telegram_channel_messages(channel_name, limit=5):
    """
    Fetches latest messages from a public Telegram channel via t.me/s/ web preview.
    Zero credentials/login required!
    """
    clean_name = channel_name.replace("@", "").replace("https://t.me/", "").replace("s/", "").strip()
    url = f"https://t.me/s/{clean_name}"
    
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=8, allow_redirects=True)
        if resp.status_code != 200 or not resp.text:
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        msg_wraps = soup.find_all("div", class_="tgme_widget_message_wrap")
        
        results = []
        for wrap in reversed(msg_wraps):
            text_el = wrap.find("div", class_="tgme_widget_message_text")
            time_el = wrap.find("time")
            if text_el:
                msg_text = text_el.get_text(separator="\n").strip()
                date_str = time_el.get("datetime", "") if time_el else ""
                
                if len(msg_text) > 10:
                    results.append({
                        "channel": f"@{clean_name}",
                        "text": msg_text,
                        "date": date_str,
                        "link": f"https://t.me/{clean_name}"
                    })
            if len(results) >= limit:
                break
        return results
    except Exception as e:
        print(f"⚠️ Telegram scrape error for @{clean_name}: {e}")
        return []

def fetch_all_telegram_channels(channels=None):
    if channels is None:
        channels = ["binance_announcements", "wublockchainenglish", "unusual_whales_news"]
    
    all_msgs = []
    for ch in channels:
        msgs = fetch_telegram_channel_messages(ch, limit=3)
        all_msgs.extend(msgs)
    return all_msgs

if __name__ == "__main__":
    msgs = fetch_all_telegram_channels(["binance_announcements"])
    print(f"Fetched {len(msgs)} Telegram messages:")
    for m in msgs:
        print(f"[{m['channel']}] {m['text'][:100]}...")
