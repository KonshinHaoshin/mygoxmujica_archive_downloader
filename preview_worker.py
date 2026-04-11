import os
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

try:
    import requests
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False
    import urllib.request


class PreviewWorker(QThread):
    finished = Signal(QPixmap, str)  # pixmap, 错误信息(为空则成功)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url
        self._is_cancelled = False

    def cancel(self):
        """通知线程尽快停止"""
        self._is_cancelled = True

    def run(self):
        try:
            if self._is_cancelled:
                return

            if _HAS_REQUESTS:
                resp = requests.get(self.url, timeout=12, stream=True)
                resp.raise_for_status()

                data = b""
                for chunk in resp.iter_content(1024):
                    if self._is_cancelled:
                        return
                    data += chunk
            else:
                with urllib.request.urlopen(self.url, timeout=12) as resp:
                    data = b""
                    while True:
                        if self._is_cancelled:
                            return
                        chunk = resp.read(1024)
                        if not chunk:
                            break
                        data += chunk

            if self._is_cancelled:
                return

            pm = QPixmap()
            if not pm.loadFromData(data):
                self.finished.emit(QPixmap(), "图片解码失败")
            else:
                self.finished.emit(pm, "")
        except Exception as e:
            if not self._is_cancelled:
                self.finished.emit(QPixmap(), f"下载失败: {e}")


class PreviewDialog(QDialog):
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图片预览")
        self.resize(640, 480)

        self.label = QLabel("正在加载...", self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.worker = PreviewWorker(url)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        self._worker_running = True

    def on_finished(self, pixmap: QPixmap, err: str):
        self._worker_running = False
        if err:
            self.label.setText(err)
        else:
            scaled = pixmap.scaled(
                self.label.width(), self.label.height(),
                aspectRatioMode=Qt.KeepAspectRatio
            )
            self.label.setPixmap(scaled)

    def closeEvent(self, event):
        if hasattr(self, "worker") and self._worker_running:
            self.worker.cancel()
            self.worker.wait()
        super().closeEvent(event)
