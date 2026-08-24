import os
import json
import datetime
import subprocess
import shutil
from llm_curator import build_obsidian_markdown

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(CURRENT_DIR, "sources.json")

def get_obsidian_bin():
    return shutil.which("obsidian") or shutil.which("obsidian-cli") or os.path.expanduser("~/.local/bin/obsidian")

def get_obsidian_vaults():
    obs_bin = get_obsidian_bin()
    if not obs_bin or not (os.path.exists(obs_bin) or shutil.which(obs_bin)):
        return ["DefaultVault"]
    try:
        proc = subprocess.run([obs_bin, "vaults"], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            lines = [l.strip() for l in proc.stdout.strip().split("\n") if l.strip()]
            return lines if lines else ["DefaultVault"]
    except Exception as e:
        print(f"⚠️ Failed listing vaults: {e}")
    return ["DefaultVault"]

def load_obsidian_config():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                return sdata.get("distribution_settings", {}).get("obsidian", {
                    "enabled": True,
                    "vault": "Investing",
                    "folder": "Daily Intel"
                })
        except Exception:
            pass
    return {"enabled": True, "vault": "Investing", "folder": "Daily Intel"}

def save_note_to_obsidian(curated_data, custom_vault=None, custom_folder=None):
    cfg = load_obsidian_config()
    vault = custom_vault or cfg.get("vault", "Investing")
    folder = (custom_folder or cfg.get("folder", "Daily Intel")).strip().strip("/")

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    file_name = f"{today_str}-晚报内参.md"
    file_path = f"{folder}/{file_name}" if folder else file_name

    md_content = build_obsidian_markdown(curated_data)

    obs_bin = get_obsidian_bin()
    if not obs_bin or not (os.path.exists(obs_bin) or shutil.which(obs_bin)):
        return {"success": False, "error": f"Obsidian CLI 路径未找到，请确保已安装 obsidian CLI"}

    try:
        # Create or overwrite file in Obsidian vault
        cmd = [
            obs_bin,
            "create",
            f"vault={vault}",
            f"path={file_path}",
            f"content={md_content}",
            "overwrite"
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            print(f"✅ 成功将晚报内参写入 Obsidian [{vault}] -> {file_path}")
            return {
                "success": True,
                "vault": vault,
                "file_path": file_path,
                "message": f"已成功在 Obsidian [{vault}] 中创建笔记: {file_path}"
            }
        else:
            err = proc.stderr or proc.stdout
            print(f"⚠️ Obsidian CLI 写入报错: {err}")
            return {"success": False, "error": f"Obsidian CLI 报错: {err}"}
    except Exception as e:
        print(f"⚠️ 执行 Obsidian 命令失败: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("Available vaults:", get_obsidian_vaults())
