# ui_main.py
import os
import sys
import subprocess
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QListWidget, QVBoxLayout, QWidget,
    QFileDialog, QComboBox, QLabel, QLineEdit, QProgressBar,
    QMessageBox, QCheckBox, QHBoxLayout
)

from announcement_dialog import AnnouncementDialog
from download_thread import DownloadThread
from github_api import list_all_files_recursive, list_folders_only, fetch_file_last_commit
from github_hosts_updater import update_github_hosts
from preview_worker import PreviewDialog
from mirror_dialog import MIRRORS

OWNER = "KonshinHaoshin"
REPO = "mygoxmujica_archive"


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def load_stylesheet():
    qss_path = os.path.join(os.path.dirname(__file__), "style.qss")
    icon_path = os.path.join(os.path.dirname(__file__), "down_arrow_cute.png").replace("\\", "/")
    with open(qss_path, encoding="utf-8") as f:
        qss = f.read()
        qss = qss.replace("url(down_arrow_cute.png)", f"url({icon_path})")
        return qss


def is_supported_archive(filename):
    return any(filename.endswith(ext) for ext in [
        ".zip", ".rar",
        ".tar", ".tar.gz", ".tgz",
        ".tar.bz2", ".tbz2",
        ".tar.xz", ".txz"
    ])


def extract_archive(file_path, extract_to):
    exe_path = resource_path("7-Zip/7z.exe")
    if not os.path.exists(exe_path):
        print("找不到 7z.exe，请确认路径正确")
        return False

    cmd = [exe_path, "x", file_path, f"-o{extract_to}", "-y"]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("使用 7-Zip 解压成功")
            return True
        else:
            print("7-Zip 解压失败：", result.stderr)
            return False
    except Exception as e:
        print("解压过程中出现异常：", e)
        return False


class TimestampWorker(QThread):
    finished = Signal(str, str)  # (file_path, 日期字符串或空)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if self._is_cancelled:
            return
        commit, err = fetch_file_last_commit(OWNER, REPO, self.file_path)
        if self._is_cancelled:
            return
        if err == "rate_limit":
            self.finished.emit(self.file_path, "__rate_limit__")
            return
        if commit:
            try:
                date_str = commit["commit"]["author"]["date"]
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                local_dt = dt.astimezone()
                formatted = local_dt.strftime("%Y-%m-%d %H:%M")
                self.finished.emit(self.file_path, formatted)
                return
            except Exception:
                pass
        self.finished.emit(self.file_path, "")


class MainWindow(QMainWindow):
    def __init__(self, default_mirror="jsdelivr"):
        super().__init__()

        with open(resource_path("style.qss"), "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

        self.setWindowIcon(QIcon(resource_path("icon.png")))
        self.setWindowTitle("mygoxmujica社区资源下载器 关注B站东山燃灯寺谢谢喵~")

        self.folder_box = QComboBox()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("输入关键字以筛选")
        self.list_widget = QListWidget()
        self.load_button = QPushButton("加载选中目录内容")
        self.download_button = QPushButton("下载选中项")
        self.preview_button = QPushButton("预览图片")
        self.stop_button = QPushButton("停止下载")
        self.stop_button.setEnabled(True)
        self.stop_button.clicked.connect(self.stop_download)

        self.mirror_box = QComboBox()
        for label, key in MIRRORS:
            self.mirror_box.addItem(label, key)
        self.mirror_box.setCurrentIndex(
            next((i for i, (_, k) in enumerate(MIRRORS) if k == default_mirror), 0)
        )
        self.list_widget.currentRowChanged.connect(self.update_file_info)
        self.last_save_dir = os.getcwd()

        self.update_hosts_button = QPushButton("更新 GitHub Hosts（需要管理员权限）")
        self.update_hosts_button.clicked.connect(self.update_github_hosts_action)

        self.announcement_button = QPushButton("查看仓库更新公告")
        self.announcement_button.clicked.connect(self.show_announcement)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        self._timestamp_cache = {}
        self._timestamp_worker = None

        layout = QVBoxLayout()
        layout.addWidget(QLabel("选择目录："))
        layout.addWidget(self.folder_box)
        layout.addWidget(self.announcement_button)
        layout.addWidget(self.load_button)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.update_hosts_button)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.download_button, 1)
        btn_row.addWidget(self.stop_button, 1)
        layout.addLayout(btn_row)

        layout.addWidget(self.preview_button)

        self.mirror_label = QLabel("选择镜像源：")
        self.mirror_desc = QLabel("""
        raw：直连 GitHub，实时源码，国内可能不稳定
        jsdelivr：CDN 加速，国内稳定，适合小/中型文件，有缓存延迟
        ghproxy.net：代理加速，支持大文件，国内可用
        ghfast.top：代理加速，备用方案
        """)
        self.mirror_desc.setWordWrap(True)

        layout.addWidget(self.mirror_label)
        layout.addWidget(self.mirror_box)
        layout.addWidget(self.mirror_desc)

        self.auto_extract_checkbox = QCheckBox("下载完成后自动解压（并删除源文件）")
        self.auto_extract_checkbox.setChecked(True)
        layout.addWidget(self.auto_extract_checkbox)

        layout.addWidget(QLabel("当前状态："))
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.load_button.clicked.connect(self.load_selected_folder_files)
        self.download_button.clicked.connect(self.download_selected)
        self.search_bar.textChanged.connect(self.filter_list)
        self.preview_button.clicked.connect(self.preview_selected)

        self.entries = []
        self.filtered_entries = []
        self.load_root_folders()

    def show_announcement(self):
        dlg = AnnouncementDialog(OWNER, REPO, self)
        dlg.exec()

    def preview_selected(self):
        idx = self.list_widget.currentRow()
        if idx == -1:
            QMessageBox.warning(self, "提示", "请先选择一个文件")
            return

        entry = self.filtered_entries[idx]
        path = entry.get("path", "").lower()
        if not any(path.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp")):
            QMessageBox.warning(self, "提示", "选中的不是图片文件")
            return

        mirror = self.mirror_box.currentData()
        owner, repo, branch = OWNER, REPO, "main"
        rel_path = entry["path"].lstrip("/")
        raw_url = entry.get("download_url") or f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{rel_path}"

        if mirror == "raw":
            url = raw_url
        elif mirror == "ghproxy.net":
            url = f"https://ghproxy.net/{raw_url}"
        elif mirror == "ghfast.top":
            url = f"https://ghfast.top/{raw_url}"
        elif mirror == "jsdelivr":
            url = f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/{rel_path}"
        else:
            url = raw_url

        dlg = PreviewDialog(url, self)
        dlg.exec()

    def update_github_hosts_action(self):
        try:
            update_github_hosts()
            QMessageBox.information(self, "Hosts 更新", "GitHub hosts 已更新完成，请刷新网络生效。")
        except Exception as e:
            QMessageBox.critical(self, "Hosts 更新失败", f"更新失败：{str(e)}\n请尝试以管理员身份运行本程序。")

    def update_file_info(self, index):
        if index < 0 or index >= len(self.filtered_entries):
            self.status_label.setText("未选择任何文件")
            return

        entry = self.filtered_entries[index]
        name = entry["path"]
        size_bytes = entry.get("size", None)

        if size_bytes is not None:
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            base_info = f"选中: {name} （大小：{size_str}）"
        else:
            base_info = f"选中: {name} （大小未知）"

        file_path = entry["path"]

        if file_path in self._timestamp_cache:
            cached = self._timestamp_cache[file_path]
            if cached == "__rate_limit__":
                self.status_label.setText(f"{base_info}\n上传时间：获取失败（API 频率限制，建议配置 GITHUB_TOKEN）")
            elif cached:
                self.status_label.setText(f"{base_info}\n上传时间：{cached}")
            else:
                self.status_label.setText(f"{base_info}\n上传时间：获取失败")
        else:
            self.status_label.setText(f"{base_info}\n正在获取上传时间...")
            self._start_timestamp_worker(file_path)

    def _start_timestamp_worker(self, file_path):
        # 取消上一个未完成的请求
        if self._timestamp_worker is not None and self._timestamp_worker.isRunning():
            self._timestamp_worker.cancel()
            self._timestamp_worker.wait()

        self._timestamp_worker = TimestampWorker(file_path)
        self._timestamp_worker.finished.connect(self.on_timestamp_loaded)
        self._timestamp_worker.start()

    def on_timestamp_loaded(self, file_path, date_str):
        self._timestamp_cache[file_path] = date_str

        # 只在当前选中文件匹配时更新 UI
        idx = self.list_widget.currentRow()
        if 0 <= idx < len(self.filtered_entries):
            current_entry = self.filtered_entries[idx]
            if current_entry["path"] == file_path:
                self.update_file_info(idx)

    def load_root_folders(self):
        folders = list_folders_only(OWNER, REPO)
        self.folder_box.clear()
        for folder in folders:
            self.folder_box.addItem(folder["name"])

    def load_selected_folder_files(self):
        folder_name = self.folder_box.currentText()
        self._timestamp_cache.clear()
        files = list_all_files_recursive(OWNER, REPO, folder_name)
        self.entries = [f for f in files if f["type"] == "file"]
        self.update_list_widget(self.entries)

    def update_list_widget(self, entries):
        self.list_widget.setUpdatesEnabled(False)
        self.list_widget.clear()
        for item in entries:
            self.list_widget.addItem(item["path"])

        self.filtered_entries = entries
        self.status_label.setText(f"共 {len(entries)} 个文件（含子目录）")

        self.list_widget.setUpdatesEnabled(True)
        self.list_widget.repaint()

    def filter_list(self, text):
        filtered = [e for e in self.entries if text.lower() in e["path"].lower()]
        self.update_list_widget(filtered)

    def download_selected(self):
        selected = self.list_widget.currentRow()
        if selected == -1:
            return

        entry = self.filtered_entries[selected]
        save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录", self.last_save_dir)
        if not save_dir:
            return
        self.last_save_dir = save_dir

        relative_path = entry["path"].replace("/", os.sep)
        save_path = os.path.join(save_dir, relative_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        mirror = self.mirror_box.currentData()

        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(f"正在下载: {save_path}")
        self.stop_button.setEnabled(True)

        self.thread = DownloadThread(entry["download_url"], save_path, mirror)
        self.thread.progress.connect(self.update_progress_bar)
        self.thread.finished.connect(self.on_download_finished)
        self.thread.start()

    def update_progress_bar(self, value):
        if self.progress_bar.minimum() == 0 and self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(value)

    def stop_download(self):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
            self.status_label.setText("用户已请求中止下载")
            self.stop_button.setEnabled(False)

    def on_download_finished(self, success, message):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText(message)
        self.stop_button.setEnabled(False)

        if success and self.auto_extract_checkbox.isChecked():
            save_path = self.thread.save_path
            if is_supported_archive(save_path):
                extract_to = os.path.dirname(save_path)
                try:
                    extracted = extract_archive(save_path, extract_to)
                    if extracted:
                        os.remove(save_path)
                        self.status_label.setText(f"{message}，已自动解压并删除源文件")
                    else:
                        self.status_label.setText(f"{message}，但解压失败")
                except Exception as e:
                    self.status_label.setText(f"{message}，解压异常：{str(e)}")
