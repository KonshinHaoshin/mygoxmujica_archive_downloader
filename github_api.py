import os

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}


def list_github_contents(owner, repo, path=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        print("网络连接失败:", exc)
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
    except Exception as exc:
        print(f"加载 {path} 失败: {exc}")
    return files


def list_folders_only(owner, repo, path=""):
    items = list_github_contents(owner, repo, path)
    return [item for item in items if item["type"] == "dir"]


def fetch_repo_commits(owner, repo, per_page=20):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page={per_page}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json(), ""
    except requests.exceptions.HTTPError as exc:
        return [], f"HTTP 错误: {exc}"
    except requests.exceptions.RequestException as exc:
        return [], f"网络连接失败: {exc}"


def fetch_commit_files(owner, repo, sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [file["filename"] for file in data.get("files", [])], ""
    except requests.exceptions.HTTPError as exc:
        return [], f"HTTP 错误: {exc}"
    except requests.exceptions.RequestException as exc:
        return [], f"网络连接失败: {exc}"


def fetch_file_last_commit(owner, repo, file_path):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?path={file_path}&per_page=1"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 403:
            return None, "rate_limit"
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0], ""
        return None, ""
    except requests.exceptions.RequestException as exc:
        return None, f"网络连接失败: {exc}"
