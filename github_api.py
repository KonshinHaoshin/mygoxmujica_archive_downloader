import requests

import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的环境变量

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

def list_github_contents(owner, repo, path=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print("❌ 网络连接失败：", e)
        return []
def list_all_files_recursive(owner, repo, path=""):
    files = []
    try:
        items = list_github_contents(owner, repo, path)
        for item in items:
            if item["type"] == "file":
                files.append(item)
            elif item["type"] == "dir":
                files.extend(list_all_files_recursive(owner, repo, item["path"]))
    except Exception as e:
        print(f"❌ 加载 {path} 失败: {e}")
    return files

def list_folders_only(owner, repo, path=""):
    items = list_github_contents(owner, repo, path)
    return [item for item in items if item["type"] == "dir"]
