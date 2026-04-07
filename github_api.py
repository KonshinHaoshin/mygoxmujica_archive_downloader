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
        print("网络连接失败：", e)
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
        print(f"加载 {path} 失败: {e}")
    return files

def list_folders_only(owner, repo, path=""):
    items = list_github_contents(owner, repo, path)
    return [item for item in items if item["type"] == "dir"]

def fetch_repo_commits(owner, repo, per_page=20):
    """获取仓库最近的 commit 列表"""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page={per_page}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json(), ""
    except requests.exceptions.HTTPError as e:
        return [], f"HTTP 错误: {e}"
    except requests.exceptions.RequestException as e:
        return [], f"网络连接失败: {e}"

def fetch_file_last_commit(owner, repo, file_path):
    """获取指定文件最后一次 commit 信息"""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?path={file_path}&per_page=1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 403:
            return None, "rate_limit"
        r.raise_for_status()
        data = r.json()
        if data:
            return data[0], ""
        return None, ""
    except requests.exceptions.RequestException as e:
        return None, f"网络连接失败: {e}"
