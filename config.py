# Configuration for Cloudflare R2, Worker Domain, and RSSHub
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

R2_CONFIG = {
    "account_id": os.getenv("R2_ACCOUNT_ID", ""),
    "access_key_id": os.getenv("R2_ACCESS_KEY_ID", ""),
    "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY", ""),
    "endpoint_url": os.getenv("R2_ENDPOINT_URL", ""),
    "bucket_name": os.getenv("R2_BUCKET_NAME", "agentfeed-public"),
    "public_domain": os.getenv("R2_PUBLIC_DOMAIN", "https://feed.your-domain.com")
}

RSSHUB_CONFIG = {
    "primary": os.getenv("RSSHUB_PRIMARY", "https://rsshub.app"),
    "backup": os.getenv("RSSHUB_BACKUP", "https://rsshub.app")
}

RSS_ROUTES = [
    "/wsj/zh-hans/markets",
    "/wsj/zh-hans/world",
    "/reuters/business/markets/us",
    "/bloomberg",
    "/cnbc/world-markets",
    "/huxiu/moment",
    "/36kr/newsflashes"
]
