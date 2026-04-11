import os

import requests

SHELTER_RAW_PREFIX = "https://raw.githubusercontent.com/KonshinHaoshin/mygoxmujica_archive/main/"
SHELTER_MIRROR_PREFIX = "https://git.shelter.net.cn/Shelter/shelter_archive/raw/branch/main/"


def convert_to_mirror(url: str, mirror="raw") -> str:
    if mirror == "ghproxy.net":
        return f"https://ghproxy.net/{url}"
    if mirror == "ghfast.top":
        return f"https://ghfast.top/{url}"
    if mirror == "jsdelivr":
        return url.replace(
            "https://raw.githubusercontent.com/",
            "https://cdn.jsdelivr.net/gh/"
        ).replace("/main/", "@main/")
    if mirror == "shelter":
        return url.replace(SHELTER_RAW_PREFIX, SHELTER_MIRROR_PREFIX)
    return url


def download_file(url, save_path, mirror="ghproxy.net"):
    real_url = convert_to_mirror(url, mirror)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        response = requests.get(real_url, timeout=20)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"下载完成: {save_path}")
    except Exception as exc:
        print(f"下载失败: {save_path}，错误信息: {exc}")


def download_file_with_progress(url, save_path, mirror="raw", progress_callback=None):
    mirrors = ["raw", "jsdelivr", "ghproxy.net", "ghfast.top", "shelter"]
    tried = []

    for current_mirror in [mirror] + [item for item in mirrors if item != mirror]:
        tried.append(current_mirror)
        real_url = convert_to_mirror(url, current_mirror)
        try:
            with requests.get(real_url, stream=True, timeout=30) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size:
                                progress_callback(int(downloaded * 100 / total_size))
            return True, current_mirror
        except Exception:
            continue

    return False, f"所有镜像均失败（尝试过：{', '.join(tried)}）"
