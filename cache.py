# cache.py — 持久化缓存，保存在 cache.json
import json
import os

_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")

_data = {
    "file_lists": {},    # folder_name -> [file entry, ...]
    "timestamps": {},    # file_path   -> date_str | "__rate_limit__"
    "commits": [],       # commit list (raw GitHub API dicts)
    "commit_files": {},  # sha -> [filename, ...]
}


def load():
    global _data
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # 合并，兼容旧版缓存文件缺字段的情况
            for key in _data:
                if key in loaded:
                    _data[key] = loaded[key]
        except Exception as e:
            print(f"缓存加载失败: {e}")


def _save():
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"缓存保存失败: {e}")


# ── 文件列表 ──────────────────────────────────────────────
def get_file_list(folder):
    return _data["file_lists"].get(folder)


def set_file_list(folder, files):
    _data["file_lists"][folder] = files
    _save()


# ── 上传时间 ──────────────────────────────────────────────
def get_all_timestamps():
    return _data["timestamps"]


def get_timestamp(file_path):
    return _data["timestamps"].get(file_path)


def set_timestamp(file_path, date_str):
    _data["timestamps"][file_path] = date_str
    _save()


# ── 仓库 commit 公告 ──────────────────────────────────────
def get_commits():
    return _data["commits"] if _data["commits"] else None


def set_commits(commits):
    _data["commits"] = commits
    _save()


# ── commit 变更文件 ───────────────────────────────────────
def get_commit_files(sha):
    return _data["commit_files"].get(sha)


def set_commit_files(sha, files):
    _data["commit_files"][sha] = files
    _save()
