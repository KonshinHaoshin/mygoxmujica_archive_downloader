# main.py
from PyQt5.QtWidgets import QApplication, QMessageBox
from ui_main import MainWindow, load_stylesheet
from mirror_dialog import MirrorSelectDialog  # <== 新增
import sys
import traceback

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())

    try:
        # ⏳ 启动前弹出镜像选择框
        dialog = MirrorSelectDialog()
        if dialog.exec_() != 1:  # 取消关闭则退出程序
            sys.exit(0)

        selected_mirror = dialog.get_selected_mirror()

        # 👇 将镜像参数传入 MainWindow
        window = MainWindow(default_mirror=selected_mirror)
        window.show()
        sys.exit(app.exec_())

    except Exception as e:
        msg = QMessageBox()
        msg.setWindowTitle("出错了")
        msg.setText("程序异常退出，请检查网络或镜像源设置")
        msg.exec_()
