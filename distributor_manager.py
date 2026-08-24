import os
import json
from distributor_feishu import send_feishu_brief, load_feishu_config
from distributor_feishu_doc import create_feishu_doc
from distributor_obsidian import save_note_to_obsidian, load_obsidian_config
from distributor_email import send_email_brief, load_email_config

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
from paths import SOURCES_FILE

def load_distribution_settings():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                return sdata.get("distribution_settings", {})
        except Exception:
            pass
    return {}

def dispatch_all_channels(curated_data, standalone_html):
    """
    Dispatches curated brief to all enabled distribution channels:
    1. Feishu Cloud Doc (Docx API / CLI)
    2. Feishu Bot Card (Webhook)
    3. Obsidian Vault Note (CLI)
    4. Email (SMTP)
    5. RSS & Web (Cloudflare R2)
    """
    settings = load_distribution_settings()
    results = {}

    doc_url = ""

    # 1. Feishu Cloud Doc (OpenAPI / CLI)
    feishu_doc_cfg = settings.get("feishu_doc", {})
    if feishu_doc_cfg.get("enabled", False):
        print("📄 [分发] 正在通过飞书 API / CLI 自动创建飞书云文档...")
        doc_res = create_feishu_doc(curated_data)
        results["feishu_doc"] = doc_res
        if doc_res.get("success"):
            doc_url = doc_res.get("doc_url", "")
            print(f"✅ 飞书云文档创建成功: {doc_url}")
    else:
        results["feishu_doc"] = {"status": "skipped", "message": "飞书云文档分发已关闭"}

    # 2. Feishu Bot Card (Webhook)
    feishu_cfg = settings.get("feishu", {})
    if feishu_cfg.get("enabled", False):
        print("🚀 [分发] 正在推送到飞书群机器人...")
        # If doc_url exists, pass it so the card can link to it
        if doc_url:
            curated_data["feishu_doc_url"] = doc_url
        results["feishu"] = send_feishu_brief(curated_data)
    else:
        results["feishu"] = {"status": "skipped", "message": "飞书群机器人分发已关闭"}

    # 3. Obsidian
    obsidian_cfg = settings.get("obsidian", {})
    if obsidian_cfg.get("enabled", False):
        print("🚀 [分发] 正在写入 Obsidian Vault 笔记...")
        results["obsidian"] = save_note_to_obsidian(curated_data)
    else:
        results["obsidian"] = {"status": "skipped", "message": "Obsidian 分发已关闭"}

    # 4. Email
    email_cfg = settings.get("email", {})
    if email_cfg.get("enabled", False):
        print("🚀 [分发] 正在发送邮件内参...")
        results["email"] = send_email_brief(standalone_html)
    else:
        results["email"] = {"status": "skipped", "message": "邮件分发已关闭"}

    # 5. RSS / Cloudflare R2 is always part of standard pipeline
    results["rss"] = {"status": "success", "message": "Cloudflare R2 RSS 与 Web 归档已同步"}

    return results
