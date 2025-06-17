from PyQt5.QtWidgets import QApplication, QMessageBox
from ui_main import MainWindow, load_stylesheet
import sys
import traceback

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet())

    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        msg = QMessageBox()
        msg.setWindowTitle("出错了")
        msg.setText("程序异常退出，请检查网络或镜像源设置")
        msg.exec_()