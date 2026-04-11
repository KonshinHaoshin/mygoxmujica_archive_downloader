from datetime import datetime

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QPushButton

import cache
from github_api import fetch_repo_commits


class AnnouncementWorker(QThread):
    finished = Signal(list, str)

    def __init__(self, owner, repo, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.repo = repo
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if self._is_cancelled:
            return
        commits, err = fetch_repo_commits(self.owner, self.repo, per_page=20)
        if not self._is_cancelled:
            self.finished.emit(commits, err)


class AnnouncementDialog(QDialog):
    def __init__(self, owner, repo, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.repo = repo
        self.setWindowTitle("仓库更新公告")
        self.resize(580, 480)

        layout = QVBoxLayout()

        title_label = QLabel("最近推送记录（最多 20 条）")
        layout.addWidget(title_label)

        self.browser = QTextBrowser()
        layout.addWidget(self.browser)

        btn_row = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._start_load)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self._worker = None
        self._worker_running = False

        # 先显示缓存
        cached = cache.get_commits()
        if cached:
            self._render(cached)
            self.refresh_btn.setText("刷新")
        else:
            self.browser.setHtml("<p>正在加载...</p>")
            self._start_load()

    def _start_load(self):
        if self._worker_running:
            return
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("正在刷新...")
        self._worker = AnnouncementWorker(self.owner, self.repo)
        self._worker.finished.connect(self._on_loaded)
        self._worker.start()
        self._worker_running = True

    def _on_loaded(self, commits, err):
        self._worker_running = False
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新")
        if err:
            self.browser.setHtml(f"<p style='color:red;'>加载失败：{err}</p>")
            return
        if not commits:
            self.browser.setHtml("<p>暂无提交记录。</p>")
            return
        cache.set_commits(commits)
        self._render(commits)

    def _render(self, commits):
        parts = []
        for c in commits:
            commit_info = c.get("commit", {})
            author_info = commit_info.get("author", {})
            message = commit_info.get("message", "").strip()
            author_name = author_info.get("name", "未知")
            date_str = author_info.get("date", "")
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                formatted_date = dt.astimezone().strftime("%Y-%m-%d %H:%M")
            except Exception:
                formatted_date = date_str
            message_html = (message
                            .replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;")
                            .replace("\n", "<br>"))
            parts.append(
                f"<p><b>{formatted_date}</b> &nbsp; {author_name}<br>{message_html}</p><hr>"
            )
        self.browser.setHtml("".join(parts))

    def closeEvent(self, event):
        if self._worker and self._worker_running:
            self._worker.cancel()
            self._worker.wait()
        super().closeEvent(event)
