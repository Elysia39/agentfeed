#!/usr/bin/env python3
"""
AgentFeed Desktop Application
=============================
Native standalone desktop wrapper that embeds the AgentFeed FastAPI Server,
Web Admin dashboard, and multi-channel distribution engine into a native window.
"""

import os
import sys
import time
import threading
import asyncio
import socket
import urllib.request
import webbrowser
import subprocess

# Ensure current directory is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Static imports so PyInstaller bundles all dependencies
import uvicorn
import server
import run_daily_brief
import paths

if hasattr(server, "ensure_full_mac_path"):
    server.ensure_full_mac_path()

def find_available_port(start_port: int = 9830, host: str = "127.0.0.1") -> int:
    """Find an available port starting from start_port."""
    for p in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex((host, p)) != 0:
                return p
    return start_port

def is_server_ready(url: str, timeout: float = 0.5) -> bool:
    """Check if the HTTP server is ready and responding."""
    try:
        req = urllib.request.Request(f"{url}/api/sources", headers={"User-Agent": "AgentFeed-Desktop"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False

def run_fastapi_server(host: str, port: int):
    """Run uvicorn server in background thread with dedicated asyncio loop."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        config = uvicorn.Config(server.app, host=host, port=port, log_level="warning", access_log=False)
        s = uvicorn.Server(config)
        loop.run_until_complete(s.serve())
    except Exception as e:
        print(f"⚠️ FastAPI Server Error: {e}", file=sys.stderr)

def send_desktop_notification(title: str, message: str):
    """Cross-platform native desktop notification."""
    try:
        if sys.platform == "darwin":
            apple_script = f'display notification "{message}" with title "{title}" subtitle "AgentFeed"'
            subprocess.run(["osascript", "-e", apple_script], capture_output=True)
        elif sys.platform.startswith("win"):
            from plyer import notification
            notification.notify(title=title, message=message, app_name="AgentFeed")
        elif sys.platform.startswith("linux"):
            subprocess.run(["notify-send", title, message], capture_output=True)
    except Exception:
        pass

def main():
    host = os.getenv("AGENTFEED_HOST", "127.0.0.1")
    port = int(os.getenv("AGENTFEED_PORT", str(find_available_port(9830, host))))
    url = f"http://{host}:{port}"

    print("=" * 65)
    print("🚀 正在启动 AgentFeed Desktop 桌面应用...")
    print(f"📡 本地后端服务端口: {url}")
    print("=" * 65)

    # 1. Start backend server in a background thread
    server_thread = threading.Thread(target=run_fastapi_server, args=(host, port), daemon=True)
    server_thread.start()

    # 2. Wait until the HTTP server is responsive
    retries = 50
    ready = False
    while retries > 0:
        if is_server_ready(url):
            ready = True
            break
        time.sleep(0.1)
        retries -= 1

    if not ready:
        print("⚠️ 后端服务启动较慢，继续尝试加载界面...")

    send_desktop_notification("AgentFeed 已就绪", "全源感知与大模型梳理中枢已就绪。")

    # 3. Launch native Webview window
    try:
        import webview
        print("🖥️ 正在载入原生桌面窗口 (Cocoa / WebKit)...")
        window = webview.create_window(
            title="AgentFeed - Universal Perception & Ingestion Hub for AI Agents",
            url=url,
            width=1280,
            height=860,
            min_size=(980, 650),
            confirm_close=False,
            text_select=True
        )
        webview.start(debug=False)
        print("👋 AgentFeed 桌面窗口已正常关闭。")
    except Exception as e:
        print(f"⚠️ 未能创建原生桌面窗口 ({e})，正在通过系统默认浏览器打开...")
        webbrowser.open(url)
        print(f"👉 请在浏览器中访问: {url}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("👋 服务已退出。")

if __name__ == "__main__":
    main()
