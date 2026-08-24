#!/usr/bin/env python3
"""
AgentFeed Desktop Application
=============================
Native desktop wrapper that embeds the AgentFeed FastAPI Server,
Web Admin dashboard, and multi-channel distribution engine into a standalone window.
"""

import os
import sys
import time
import threading
import socket
import webbrowser
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def run_fastapi_server(host: str = "127.0.0.1", port: int = 9830):
    """Run uvicorn server in background thread."""
    try:
        import uvicorn
        from server import app
        config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        print(f"⚠️ FastAPI Server Error: {e}")

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
    port = int(os.getenv("AGENTFEED_PORT", "9830"))
    url = f"http://{host}:{port}"

    print("=" * 65)
    print("🚀 正在启动 AgentFeed Desktop 桌面应用...")
    print(f"📡 本地后端服务端口: {url}")
    print("=" * 65)

    # 1. Start backend server if port is not already running
    if not is_port_in_use(port, host):
        t = threading.Thread(target=run_fastapi_server, args=(host, port), daemon=True)
        t.start()
        # Wait until server is live
        retries = 30
        while retries > 0:
            if is_port_in_use(port, host):
                break
            time.sleep(0.1)
            retries -= 1

    time.sleep(0.3)
    send_desktop_notification("AgentFeed 已就绪", "全源感知与大模型梳理中枢已在后台常驻运行。")

    # 2. Try launching native Webview window
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
        print("👋 AgentFeed 桌面窗口已关闭。")
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
