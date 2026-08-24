import os
import sys

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    candidates = [
        os.path.join(base_path, relative_path),
        os.path.join(base_path, "_internal", relative_path),
        os.path.join(os.path.dirname(base_path), relative_path),
        os.path.join(os.getcwd(), relative_path)
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return os.path.join(base_path, relative_path)

USER_DATA_DIR = os.path.expanduser("~/.agentfeed")
os.makedirs(USER_DATA_DIR, exist_ok=True)

SOURCES_FILE = os.path.join(USER_DATA_DIR, "sources.json")
HISTORY_FILE = os.path.join(USER_DATA_DIR, "feed_history.json")

# If ~/.agentfeed/sources.json does not exist, copy from bundle
if not os.path.exists(SOURCES_FILE) or os.path.getsize(SOURCES_FILE) == 0:
    for candidate in ["sources.json", "sources.example.json"]:
        src = get_resource_path(candidate)
        if os.path.exists(src) and os.path.getsize(src) > 0:
            try:
                import shutil
                shutil.copyfile(src, SOURCES_FILE)
                break
            except Exception:
                pass

HTML_FILE = get_resource_path("web_admin.html")
ICON_FILE = get_resource_path("icon.png")
