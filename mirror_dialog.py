# mirror_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton

class MirrorSelectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("选择默认镜像源")
        self.setFixedWidth(400)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("请选择一个默认镜像源："))

        self.mirror_box = QComboBox()
        self.mirror_box.addItems(["ghproxy", "jsdelivr", "tbedu", "raw"])
        self.mirror_box.setCurrentText("jsdelivr")
        layout.addWidget(self.mirror_box)

        confirm_btn = QPushButton("确定")
        confirm_btn.clicked.connect(self.accept)
        layout.addWidget(confirm_btn)

        self.setLayout(layout)

    def get_selected_mirror(self):
        return self.mirror_box.currentText()
