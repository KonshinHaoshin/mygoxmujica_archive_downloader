# preview_worker.py
import os
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

try:
    import requests
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False
    import urllib.request


class PreviewWorker(QThread):
    finished = pyqtSignal(QPixmap, str)  # pixmap, 错误信息(为空则成功)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            if _HAS_REQUESTS:
                resp = requests.get(self.url, timeout=12)
                resp.raise_for_status()
                data = resp.content
            else:
                with urllib.request.urlopen(self.url, timeout=12) as resp:
                    data = resp.read()

            pm = QPixmap()
            if not pm.loadFromData(data):
                self.finished.emit(QPixmap(), "❌ 图片解码失败")
            else:
                self.finished.emit(pm, "")
        except Exception as e:
            self.finished.emit(QPixmap(), f"⚠️ 下载失败: {e}")


class PreviewDialog(QDialog):
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图片预览")
        self.resize(640, 480)

        self.label = QLabel("⏳ 正在加载...", self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # 开启线程加载
        self.worker = PreviewWorker(url)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, pixmap: QPixmap, err: str):
        if err:
            self.label.setText(err)
        else:
            scaled = pixmap.scaled(
                self.label.width(), self.label.height(),
                aspectRatioMode=1  # 等比例
            )
            self.label.setPixmap(scaled)
