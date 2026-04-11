# mirror_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton


MIRRORS = [
    ("raw（直连 GitHub，实时但国内不稳定）", "raw"),
    ("jsdelivr（CDN 加速，国内稳定，有缓存延迟）", "jsdelivr"),
    ("ghproxy.net（代理加速，支持大文件）", "ghproxy.net"),
    ("ghfast.top（代理加速，备用）", "ghfast.top"),
]


class MirrorSelectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("选择默认镜像源")
        self.setFixedWidth(460)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("请选择一个默认镜像源："))

        self.mirror_box = QComboBox()
        for label, key in MIRRORS:
            self.mirror_box.addItem(label, key)
        self.mirror_box.setCurrentIndex(0)  # 默认 raw
        layout.addWidget(self.mirror_box)

        confirm_btn = QPushButton("确定")
        confirm_btn.clicked.connect(self.accept)
        layout.addWidget(confirm_btn)

        self.setLayout(layout)

    def get_selected_mirror(self):
        return self.mirror_box.currentData()
