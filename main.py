# -*- coding: UTF-8 -*-


import sys
import time

# from PyQt5 import sip
#
# if hasattr(sys, 'frozen'):
#     os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QPixmap, QFont

from mainwindow import MyMainWindow, BASE_DIR

if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)  # 自适应分辨率
    QtWidgets.QApplication.setQuitOnLastWindowClosed(False)
    app = QtWidgets.QApplication(sys.argv)
    splash = QtWidgets.QSplashScreen(QPixmap(f"{BASE_DIR / 'owl_256.png'}"))
    splash.setFont(QFont("microsoft yahei", 12, QFont.Bold))
    splash.showMessage("欢迎使用Android Tools !", QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom, QtCore.Qt.cyan)
    splash.show()  # 显示启动界面
    time.sleep(1)
    QtWidgets.qApp.processEvents()  # 处理主进程事件
    ui = MyMainWindow()
    ui.show()
    splash.finish(ui)
    sys.exit(app.exec_())
