from PyQt5.QtCore import QThread, pyqtSignal
import requests
import os

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, save_path, mirror="ghproxy"):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.mirror = mirror
        self._is_running = True

    def stop(self):
        self._is_running = False


    def run(self):
        real_url = self.convert_to_mirror(self.url, self.mirror)
        try:
            with requests.get(real_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
                with open(self.save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not self._is_running:
                            self.finished.emit(False, "❌ 下载已取消")
                            return
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                percent = int(downloaded * 100 / total_size)
                                self.progress.emit(percent)
            self.finished.emit(True, f"✅ 下载完成: {self.save_path}")
        except Exception as e:
            self.finished.emit(False, f"❌ 下载失败: {e}")

    def convert_to_mirror(self, url, mirror):
        if mirror == "ghproxy":
            return f"https://ghproxy.com/{url}"
        elif mirror == "jsdelivr":
            return url.replace("https://raw.githubusercontent.com/", "https://cdn.jsdelivr.net/gh/").replace("/main/", "@main/")
        return url
