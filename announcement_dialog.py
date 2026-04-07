from datetime import datetime, timezone

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextBrowser, QPushButton

from github_api import fetch_repo_commits


class AnnouncementWorker(QThread):
    finished = Signal(list, str)  # (commits 列表, 错误信息)

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
        self.setWindowTitle("仓库更新公告")
        self.resize(580, 480)

        layout = QVBoxLayout()

        title_label = QLabel("最近推送记录（最多 20 条）")
        layout.addWidget(title_label)

        self.browser = QTextBrowser()
        self.browser.setHtml("<p>正在加载...</p>")
        layout.addWidget(self.browser)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)

        self.worker = AnnouncementWorker(owner, repo)
        self.worker.finished.connect(self._on_loaded)
        self.worker.start()
        self._worker_running = True

    def _on_loaded(self, commits, err):
        self._worker_running = False
        if err:
            self.browser.setHtml(f"<p style='color:red;'>加载失败：{err}</p>")
            return
        if not commits:
            self.browser.setHtml("<p>暂无提交记录。</p>")
            return

        parts = []
        for c in commits:
            commit_info = c.get("commit", {})
            author_info = commit_info.get("author", {})
            message = commit_info.get("message", "").strip()
            author_name = author_info.get("name", "未知")
            date_str = author_info.get("date", "")

            # 将 UTC ISO 8601 转换为本地时间
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                local_dt = dt.astimezone()
                formatted_date = local_dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                formatted_date = date_str

            # 多行 commit message 处理
            message_html = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

            parts.append(
                f"<p>"
                f"<b>{formatted_date}</b> &nbsp; {author_name}<br>"
                f"{message_html}"
                f"</p>"
                f"<hr>"
            )

        self.browser.setHtml("".join(parts))

    def closeEvent(self, event):
        if hasattr(self, "worker") and self._worker_running:
            self.worker.cancel()
            self.worker.wait()
        super().closeEvent(event)
