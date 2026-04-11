from PySide6.QtWidgets import QApplication, QMessageBox
from ui_main import MainWindow, load_stylesheet
from mirror_dialog import MirrorSelectDialog
import sys


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())

    try:
        dialog = MirrorSelectDialog()
        if dialog.exec() != 1:
            sys.exit(0)

        selected_mirror = dialog.get_selected_mirror()

        window = MainWindow(default_mirror=selected_mirror)
        window.show()
        sys.exit(app.exec())

    except Exception:
        msg = QMessageBox()
        msg.setWindowTitle("出错了")
        msg.setText("程序异常退出，请检查网络或镜像源设置")
        msg.exec()
