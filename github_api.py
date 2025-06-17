import requests

def list_github_contents(owner, repo, path=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

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
