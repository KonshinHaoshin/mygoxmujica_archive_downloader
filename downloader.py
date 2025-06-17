import requests
import os

def convert_to_mirror(url: str, mirror="ghproxy") -> str:
    if mirror == "ghproxy":
        return f"https://ghproxy.com/{url}"
    elif mirror == "jsdelivr":
        # 转换 raw.githubusercontent 链接为 jsDelivr 格式
        # 示例：raw.githubusercontent.com/user/repo/main/path → cdn.jsdelivr.net/gh/user/repo@main/path
        return url.replace(
            "https://raw.githubusercontent.com/",
            "https://cdn.jsdelivr.net/gh/"
        ).replace("/main/", "@main/")
    else:
        return url  # 默认不修改

def download_file(url, save_path, mirror="ghproxy"):
    real_url = convert_to_mirror(url, mirror)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        r = requests.get(real_url, timeout=20)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(r.content)
        print(f"✅ 下载完成: {save_path}")
    except Exception as e:
        print(f"❌ 下载失败: {save_path}，错误信息: {e}")


def download_file_with_progress(url, save_path, mirror="ghproxy", progress_callback=None):
    mirrors = ["ghproxy", "jsdelivr", "raw"]
    tried = []

    for current_mirror in [mirror] + [m for m in mirrors if m != mirror]:
        tried.append(current_mirror)
        real_url = convert_to_mirror(url, current_mirror)
        try:
            with requests.get(real_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size:
                                percent = int(downloaded * 100 / total_size)
                                progress_callback(percent)
            return True, f"{current_mirror}"
        except Exception as e:
            continue  # 尝试下一个镜像

    return False, f"所有镜像均失败（尝试过：{', '.join(tried)}）"
