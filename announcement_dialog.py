from datetime import datetime
from html import escape

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QSizePolicy
)

import cache
from github_api import fetch_repo_commits, fetch_commit_files


def force_line_breaks(text, max_chars=48):
    wrapped_lines = []
    for line in str(text).splitlines() or [""]:
        if not line:
            wrapped_lines.append("")
            continue
        while len(line) > max_chars:
            wrapped_lines.append(line[:max_chars])
            line = line[max_chars:]
        wrapped_lines.append(line)
    return "\n".join(wrapped_lines)


def forced_wrap_label(text):
    safe_text = escape(force_line_breaks(text))
    label = QLabel(f'<span style="white-space: pre-wrap;">{safe_text}</span>')
    label.setTextFormat(Qt.RichText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    label.setMinimumWidth(0)
    return label


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


class CommitFilesWorker(QThread):
    finished = Signal(str, list, str)

    def __init__(self, owner, repo, sha, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.repo = repo
        self.sha = sha

    def run(self):
        files, err = fetch_commit_files(self.owner, self.repo, self.sha)
        self.finished.emit(self.sha, files, err)


class CommitWidget(QFrame):
    def __init__(self, owner, repo, commit_data, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.repo = repo
        self.sha = commit_data.get("sha", "")
        self._files_worker = None

        self.setFrameShape(QFrame.StyledPanel)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(4)

        header_row = QHBoxLayout()

        commit_info = commit_data.get("commit", {})
        author_info = commit_info.get("author", {})
        message = commit_info.get("message", "").strip().splitlines()[0]
        author_name = author_info.get("name", "未知")
        date_str = author_info.get("date", "")
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            formatted_date = dt.astimezone().strftime("%Y-%m-%d %H:%M")
        except Exception:
            formatted_date = date_str

        meta_label = QLabel(f"<b>{formatted_date}</b>  {escape(author_name)}")
        meta_label.setTextFormat(Qt.RichText)
        meta_label.setWordWrap(True)
        meta_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        meta_label.setMinimumWidth(0)
        header_row.addWidget(meta_label, 1)

        self.toggle_btn = QPushButton("展开文件")
        self.toggle_btn.setMinimumWidth(96)
        self.toggle_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toggle_btn.clicked.connect(self._toggle)
        header_row.addWidget(self.toggle_btn)

        root.addLayout(header_row)

        msg_label = forced_wrap_label(message)
        root.addWidget(msg_label)

        self.files_widget = QWidget()
        self.files_layout = QVBoxLayout(self.files_widget)
        self.files_layout.setContentsMargins(12, 0, 0, 0)
        self.files_layout.setSpacing(1)
        self.files_widget.setVisible(False)
        root.addWidget(self.files_widget)

        self._expanded = False
        self._loaded = False

        cached = cache.get_commit_files(self.sha)
        if cached is not None:
            self._fill_files(cached)
            self._loaded = True

    def _toggle(self):
        self._expanded = not self._expanded
        self.toggle_btn.setText("收起文件" if self._expanded else "展开文件")
        self.files_widget.setVisible(self._expanded)

        if self._expanded and not self._loaded:
            self._fetch_files()

    def _fetch_files(self):
        self.toggle_btn.setEnabled(False)
        self._files_worker = CommitFilesWorker(self.owner, self.repo, self.sha)
        self._files_worker.finished.connect(self._on_files_loaded)
        self._files_worker.start()

    def _on_files_loaded(self, sha, files, err):
        self.toggle_btn.setEnabled(True)
        self._loaded = True
        if err:
            label = forced_wrap_label(f"获取失败：{err}")
            self.files_layout.addWidget(label)
        else:
            cache.set_commit_files(sha, files)
            self._fill_files(files)

    def _fill_files(self, files):
        while self.files_layout.count():
            item = self.files_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not files:
            self.files_layout.addWidget(forced_wrap_label("（无变更文件）"))
        else:
            for file_path in files:
                label = forced_wrap_label(f"• {file_path}")
                self.files_layout.addWidget(label)


class AnnouncementDialog(QDialog):
    def __init__(self, owner, repo, parent=None):
        super().__init__(parent)
        self.owner = owner
        self.repo = repo
        self.setWindowTitle("仓库更新公告")
        self.resize(620, 560)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("最近推送记录（最多 20 条）"))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(6)
        self.content_layout.addStretch()
        self.scroll.setWidget(self.content_widget)
        layout.addWidget(self.scroll)

        btn_row = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._start_load)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._worker = None
        self._worker_running = False

        cached = cache.get_commits()
        if cached:
            self._render(cached)
        else:
            self._set_placeholder("正在加载...")
            self._start_load()

    def _set_placeholder(self, text):
        self._clear_content()
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        self.content_layout.insertWidget(0, label)

    def _clear_content(self):
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
            self._set_placeholder(f"加载失败：{err}")
            return
        if not commits:
            self._set_placeholder("暂无提交记录。")
            return
        cache.set_commits(commits)
        self._render(commits)

    def _render(self, commits):
        self._clear_content()
        for index, commit_data in enumerate(commits):
            widget = CommitWidget(self.owner, self.repo, commit_data)
            self.content_layout.insertWidget(index, widget)

    def closeEvent(self, event):
        if self._worker and self._worker_running:
            self._worker.cancel()
            self._worker.wait()
        super().closeEvent(event)
