from PyQt5.QtWidgets import QApplication
from ui_main import MainWindow
import sys
import traceback

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print("程序异常退出：", e)
        traceback.print_exc()
        input("按任意键退出")
