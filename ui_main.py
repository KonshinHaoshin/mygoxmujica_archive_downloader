import stat
import subprocess
import sys

from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QListWidget, QVBoxLayout, QWidget,
    QFileDialog, QComboBox, QLabel, QLineEdit, QApplication, QProgressBar, QMessageBox
)
from PyQt5.QtWidgets import QCheckBox
import chardet

from download_thread import DownloadThread
from github_api import list_github_contents, list_all_files_recursive, list_folders_only
from downloader import download_file, download_file_with_progress
import os
from PyQt5.QtGui import QIcon
import shutil
import tarfile
import zipfile

from github_hosts_updater import update_github_hosts


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
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
        ".zip", ".rar",  # 👈 加入 .rar 支持
        ".tar", ".tar.gz", ".tgz",
        ".tar.bz2", ".tbz2",
        ".tar.xz", ".txz"
    ])




def extract_archive(file_path, extract_to):
    exe_path = resource_path("7-Zip/7z.exe") # 确保路径正确
    if not os.path.exists(exe_path):
        print("❌ 找不到 7z.exe，请确认路径正确")
        return False

    cmd = [exe_path, "x", file_path, f"-o{extract_to}", "-y"]  # -y 自动确认
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("✅ 使用 7-Zip 解压成功")
            return True
        else:
            print("❌ 7-Zip 解压失败：", result.stderr)
            return False
    except Exception as e:
        print("❌ 解压过程中出现异常：", e)
        return False


class MainWindow(QMainWindow):
    def __init__(self, default_mirror="jsdelivr"):  # <== 新增参数
        super().__init__()

        with open(resource_path("style.qss"), "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

        self.setWindowIcon(QIcon(resource_path("icon.png")))

        self.setWindowTitle("mygoxmujica社区资源下载器 关注B站东山燃灯寺谢谢喵~")
        # 控件
        self.folder_box = QComboBox()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 输入关键字以筛选")
        self.list_widget = QListWidget()
        self.load_button = QPushButton("加载选中目录内容")
        self.download_button = QPushButton("下载选中项")
        self.stop_button = QPushButton("🛑 停止下载")
        self.stop_button.setEnabled(True)
        self.stop_button.clicked.connect(self.stop_download)

        self.mirror_box = QComboBox()
        self.mirror_box.addItems(["jsdelivr", "raw", "ghproxy", "tbedu"])
        self.mirror_box.setCurrentText(default_mirror)
        self.list_widget.currentRowChanged.connect(self.update_file_info)
        self.last_save_dir = os.getcwd()  # 记住上次选择的目录

        self.update_hosts_button = QPushButton("💻 更新 GitHub Hosts（需要管理员权限）")
        self.update_hosts_button.clicked.connect(self.update_github_hosts_action)

        # 输出控件先创建，防止后续调用报错
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(QLabel("选择目录："))
        layout.addWidget(self.folder_box)
        layout.addWidget(self.load_button)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.update_hosts_button)
        layout.addWidget(self.download_button)
        layout.addWidget(self.stop_button)

        self.mirror_label = QLabel("选择镜像源：")
        self.mirror_desc = QLabel("""
        🔹 jsdelivr：✅ 国内高速稳定，适合小/中级文件，仅对更新有缓存延迟  
        🔹 raw：直连 GitHub，实时源码，适合调试，但国内不稳定  
        🔹 ghproxy：备用方案，但已不可靠，易超时或无响应  
        🔹 tbedu：📦 新增！tbedu 直链镜像，适合 raw.githubusercontent 文件加速
        """)

        self.mirror_desc.setWordWrap(True)

        layout.addWidget(self.mirror_label)
        layout.addWidget(self.mirror_box)
        layout.addWidget(self.mirror_desc)

        self.auto_extract_checkbox = QCheckBox("下载完成后自动解压（并删除源文件）")
        self.auto_extract_checkbox.setChecked(True)  # 默认开启
        layout.addWidget(self.auto_extract_checkbox)

        # 加入状态显示和进度条
        layout.addWidget(QLabel("⬇ 当前状态："))
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 信号连接
        self.load_button.clicked.connect(self.load_selected_folder_files)
        self.download_button.clicked.connect(self.download_selected)
        self.search_bar.textChanged.connect(self.filter_list)

        # 初始化
        self.entries = []
        self.filtered_entries = []
        self.load_root_folders()

    def update_github_hosts_action(self):
        try:
            update_github_hosts()
            QMessageBox.information(self, "Hosts 更新", "✅ GitHub hosts 已更新完成，请刷新网络生效。")
        except Exception as e:
            QMessageBox.critical(self, "Hosts 更新失败", f"❌ 更新失败：{str(e)}\n请尝试以管理员身份运行本程序。")


    def update_file_info(self, index):
        if index < 0 or index >= len(self.filtered_entries):
            self.status_label.setText("📂 未选择任何文件")
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
            self.status_label.setText(f"📁 选中: {name} (大小：{size_str})")
        else:
            self.status_label.setText(f"📁 选中: {name} (大小未知)")

    def load_root_folders(self):
        folders = list_folders_only("KonshinHaoshin", "mygoxmujica_archive")
        self.folder_box.clear()
        for folder in folders:
            self.folder_box.addItem(folder["name"])

    def load_selected_folder_files(self):
        folder_name = self.folder_box.currentText()
        files = list_all_files_recursive("KonshinHaoshin", "mygoxmujica_archive", folder_name)
        self.entries = [f for f in files if f["type"] == "file"]
        self.update_list_widget(self.entries)

    def update_list_widget(self, entries):
        self.list_widget.setUpdatesEnabled(False)  # 暂停刷新

        self.list_widget.clear()
        for item in entries:
            self.list_widget.addItem(item["path"])

        self.filtered_entries = entries
        self.status_label.setText(f"📄 共 {len(entries)} 个文件（含子目录）")

        self.list_widget.setUpdatesEnabled(True)  # 恢复并强制刷新
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
        mirror = self.mirror_box.currentText()

        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.status_label.setText(f"⬇ 正在下载: {save_path}")
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
            self.status_label.setText("🚩 用户已请求中止下载")
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
