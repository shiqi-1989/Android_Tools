# -*- coding: UTF-8 -*-
import platform
import sys
import time
import webbrowser
from collections import deque
from functools import reduce
from pathlib import Path

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import pyqtSlot, QEvent, QObject, QRegExp, Qt
from PyQt5.QtGui import QCursor, QRegExpValidator, QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QListView, QLabel, QAction, QMenu, QSystemTrayIcon, \
    QCompleter

from ADBTheard import *
from adb_beifen import Ui_MainWindow
from readConfig import ReadConfig, BASE_DIR

# logo = BASE_DIR / "owl.icns"
logo = BASE_DIR / "logo48.png"

result = BASE_DIR / "result"

if not result.exists():
    result.mkdir()
platform = platform.system()


class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        # self.icon = QtGui.QIcon()
        # self.icon.addPixmap(QtGui.QPixmap(":/logo/adb.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setupUi(self)
        self.tray_config()
        self.comboBox.setView(QListView())
        self.lable_no = QLabel('没有内容')
        self.lable_no.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.gridLayout_2.addWidget(self.lable_no, 0, 0, 1, 1)
        self.lable_no.setHidden(True)
        # self.lineEdit.installEventFilter(QEventHandler(self))
        self.pid = {'pid_list': []}
        self.video_time = None
        self.history = ReadConfig().get_history()
        self.phone_list = eval(ReadConfig().get_phone())
        self.queue_phone = deque([], maxlen=10)
        self.queue_phone.extend(self.phone_list)
        self.devices = {}
        self.refresh_dev()
        self.comboBox.currentIndexChanged[str].connect(self.comboBox_changed)
        self.listWidget.itemClicked.connect(self.listWidget_clicked)
        # 添加LineEdit 手机号正则校验
        # reg = QRegExp('^1(3[0-9]|4[579]|5[0-3,5-9]|6[6]|7[0135678]|8[0-9]|9[89])\d{8}$')
        reg = QRegExp(r'^1(3[0-9]|4[0-9]|5[0-9]|6[0-9]|7[0-9]|8[0-9]|9[0-9])\d{8}$')
        phone_reg = QRegExpValidator(reg)
        self.lineEdit_2.setValidator(phone_reg)
        # 添加LineEdit 手机号正则校验
        self.init_lineedit()
        # self.init_combobox()

    # logcat 日志
    @pyqtSlot()
    def on_pushButton_clicked(self):
        name = self.pushButton.text()
        product, device = self.get_product()
        if not device:
            self.call_back('未选择设备')
            return
        if name == "日志":
            cur = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            command = f"adb -s {device} logcat -v time > {result}/{product}_{cur}_logcat.log"
            self.call_back(f'---------->设备 {product} 开始捕获日志')
            self.call_back(command)
            self.thread = AdbThead(cmd=command, mode=1, pid=self.pid, dev=device, product=product)
            self.thread.signal.connect(self.call_back)
            self.thread.start()  # 启动线程
            self.pushButton.setText("停止日志")
            self.pushButton.setStyleSheet('''
                color:white;
                border-color:red;
                background-color: red;
            ''')
        elif name == '停止日志':
            pid = self.pid.get(device)
            if platform == 'Darwin':
                p_cmd = f"kill -9 {pid}"
            elif platform == 'Windows':
                p_cmd = f"taskkill /F /T /PID {pid}"
            sh = run_cmd(p_cmd)
            sh.wait()
            self.pushButton.setText("日志")
            self.pushButton.setStyleSheet('''
                        QPushButton{
                            color: rgb(106, 106, 106);
                            border-color:rgb(158, 158, 158);
                            background-color: white;
                        }
                        QPushButton:hover{
                            color: white;
                            background-color: rgb(111, 172, 236);
                            border-color:rgb(111, 172, 236);        
                        }
                    ''')

    # 安装apk
    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        product, device = self.get_product()
        if device:
            file_name, file_Type = QFileDialog.getOpenFileName(self,
                                                               "选取文件",
                                                               self.history,
                                                               "All Files (*);;APK Files (*.apk)")
            if file_name:
                self.history = str(Path(file_name).parent)
                self.call_back(f'---------->设备 {product} 开始安装')
                command = f'adb -s {device} install -r {file_name}'
                self.call_back(command)
                self.thread = AdbThead(cmd=command, mode=2, pid=self.pid, product=product)
                self.thread.signal.connect(self.call_back)
                self.thread.start()  # 启动线程
            else:
                self.call_back('未选择apk')
        else:
            self.call_back('未选择设备')

    # 刷新 设备列表
    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        self.comboBox.clear()
        self.devices.clear()
        self.refresh_dev()

    # 截图
    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        product, device = self.get_product()
        if device:
            cur_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            self.call_back(f'---------->设备 {product} 开始截图')
            command = f"adb -s {device} shell screencap -p /sdcard/screenshot_{cur_time}.png&&" \
                      f"adb -s {device} pull /sdcard/screenshot_{cur_time}.png {result}/screenshot_{cur_time}_.png "
            self.call_back(command)
            self.thread = AdbThead(cmd=command, mode=5, pid=self.pid)
            self.thread.signal.connect(self.call_back)
            self.thread.start()  # 启动线程

        else:
            self.call_back('未选择设备')

    # 录屏
    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        product, device = self.get_product()
        if device:
            cur_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            self.video_time = cur_time
            # command = f"adb -s {device} shell screenrecord /sdcard/{cur_time}.mp4"
            command = f"scrcpy -s {device} -m 1920 --show-touches --stay-awake --record {result}/{cur_time}.mp4"
            self.call_back(f"---------->设备 {product} 录屏开始")
            self.call_back(command)
            self.thread = AdbThead(cmd=command, mode=6, pid=self.pid, product=product)
            self.thread.signal.connect(self.call_back)
            self.thread.start()  # 启动线程
        else:
            self.call_back('未选择设备')

    # push文件
    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        product, device = self.get_product()
        if device:
            file_path, file_Type = QFileDialog.getOpenFileName(self,
                                                               "选取文件",
                                                               self.history,
                                                               "All Files (*)")
            if file_path:
                self.history = str(Path(file_path).parent)
                file_name = file_path.split('/')[-1]
                self.call_back(f'---------->设备 {product} 推送文件')
                command = f'adb -s {device} push {file_path} sdcard/{file_name}'
                self.call_back(command)
                self.thread = AdbThead(cmd=command, mode=7, pid=self.pid)
                self.thread.signal.connect(self.call_back)
                self.thread.start()  # 启动线程
            else:
                self.call_back('未选择文件')
        else:
            self.call_back('未选择设备')

    # push文件夹
    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        product, device = self.get_product()
        if device:
            directory = QFileDialog.getExistingDirectory(self,
                                                         "选取文件夹",
                                                         self.history)
            if directory:
                self.history = directory
                phone_path = f"{directory.split('/')[-1]}"
                self.call_back(f'---------->设备 {product} 推送文件夹')
                command = f'adb -s {device} push {directory} /sdcard/{phone_path}'
                self.call_back(command)
                self.thread = AdbThead(cmd=command, mode=8, pid=self.pid)
                self.thread.signal.connect(self.call_back)
                self.thread.start()  # 启动线程
            else:
                self.call_back('未选择文件夹')
        else:
            self.call_back('未选择设备')

    # 保存
    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        cur_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        text = self.textBrowser.toPlainText()
        try:
            with open(f'{result}/{cur_time}.log', 'w', encoding='utf-8') as f:
                f.write(text)
            self.textBrowser.append('保存成功！\r\n')
        except Exception as e:
            self.textBrowser.append(str(e))

    # 清空
    @pyqtSlot()
    def on_pushButton_10_clicked(self):
        self.textBrowser.clear()

    # 投屏
    @pyqtSlot()
    def on_pushButton_11_clicked(self):
        product, device = self.get_product()
        if device:
            command = f"scrcpy -s {device} --show-touches --stay-awake -m 1920"
            self.call_back(f"---------->设备 {product} 投屏开始")
            self.call_back(command)
            self.thread = AdbThead(cmd=command, mode=11, pid=self.pid, product=product)
            self.thread.signal.connect(self.call_back)
            self.thread.start()  # 启动线程
        else:
            self.call_back('未选择设备')

    # 查看结果文件
    @pyqtSlot()
    def on_pushButton_12_clicked(self):
        """打开系统文件资源管理器的对应文件夹"""
        try:
            # subprocess.call(["open", result])
            webbrowser.open(result)
        except Exception as e:
            self.call_back(str(e))

    # 获取包名
    @pyqtSlot()
    def on_pushButton_13_clicked(self):
        product, device = self.get_product()
        if device:
            self.call_back(f'---------->设备 {product} 获取包名')
            command = f'adb -s {device} shell dumpsys window | findstr mCurrentFocus'
            self.call_back(command)
            sh = run_cmd(command)
            self.call_back(read_sh(sh))
            self.call_back('---------->获取结束\r\n')
        else:
            self.call_back('未选择设备')

    # 清理缓存
    @pyqtSlot()
    def on_pushButton_14_clicked(self):
        product, device = self.get_product()
        if device:
            package = self.lineEdit.text()
            if package:
                self.call_back(f'---------->设备 {product} 清理缓存')
                command = f'adb -s {device} shell pm clear {package}'
                self.call_back(command)
                self.thread = AdbThead(cmd=command, mode=14, pid=self.pid)
                self.thread.signal.connect(self.call_back)
                self.thread.start()  # 启动线程
            else:
                self.call_back('请输入包名')
        else:
            self.call_back('未选择设备')

    # 卸载apk
    @pyqtSlot()
    def on_pushButton_15_clicked(self):
        product, device = self.get_product()
        if device:
            package = self.lineEdit.text()
            if package:
                self.call_back(f'---------->设备 {product} 开始卸载')
                command = f'adb -s {device} uninstall {package}'
                self.call_back(command)
                self.thread = AdbThead(cmd=command, mode=15, pid=self.pid)
                self.thread.signal.connect(self.call_back)
                self.thread.start()  # 启动线程
            else:
                self.call_back('请输入包名')
        else:
            self.call_back('未选择设备')

    # 停止monkey
    @pyqtSlot()
    def on_pushButton_16_clicked(self):
        product, device = self.get_product()
        if device:
            pid_list = get_adb_pid(device, 'monkey')
            if pid_list:
                for pid in pid_list:
                    run_cmd(f'adb -s {device} shell kill {pid}')
                self.call_back(f"---------->设备 {product} 主动停止monkey")
            else:
                self.call_back(f"---------->设备 {product} 没有执行中的monkey")
        else:
            self.call_back('未选择设备')

    # adb重启
    @pyqtSlot()
    def on_pushButton_17_clicked(self):
        command = 'adb kill-server&&adb start-server'
        self.call_back('---------->重启adb')
        self.call_back(command)
        self.thread = AdbThead(cmd=command, mode=17, pid=self.pid)
        self.thread.signal.connect(self.call_back)
        self.thread.start()  # 启动线程

    # 刷新三方包列表
    @pyqtSlot()
    def on_pushButton_18_clicked(self):
        product = self.comboBox.currentText()
        device = self.devices.get(product)
        if device:
            self.pushButton_18.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.listWidget.clear()
            self.lable_no.clear()
            command = f'adb -s {device} shell pm list package -3'
            self.thread = GetPack(command, self.listWidget)
            self.thread.signal.connect(self.call_back)
            self.thread.start()  # 启动线程

    # 获取alpha验证码
    @pyqtSlot()
    def on_pushButton_19_clicked(self):
        phone_num = self.lineEdit_2.text()
        if phone_num:
            self.thread = GetMsg(phone=phone_num, env='alpha')
            self.thread.signal.connect(self.call_back)
            self.thread.start()  # 启动线程
            self.queue_phone.append(phone_num)
            self.init_lineedit()
        else:
            self.call_back('请输入手机号！')

    # 获取pre验证码
    @pyqtSlot()
    def on_pushButton_20_clicked(self):
        phone_num = self.lineEdit_2.text()
        if phone_num:
            self.thread = GetMsg(phone=phone_num, env='pre')
            self.thread.signal.connect(self.call_back)
            self.thread.start()  # 启动线程
            self.queue_phone.append(phone_num)
            self.init_lineedit()
        else:
            self.call_back('请输入手机号！')

    # monkey
    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        product, device = self.get_product()
        if device:
            command = f'adb -s {device} shell monkey'
            package = self.package_apk.text()
            if package:
                command += f' -p {package}'
            else:
                self.call_back('请输入包名')
                return
            seed = self.seed.text()
            if seed:
                command += f' -s {seed}'
            else:
                self.call_back('请输入seed值')
                return
            throttle = self.throttle.text()
            if throttle:
                command += f' --throttle {throttle}'
            else:
                self.call_back('请输入延迟时间')
                return
            level = self.level.text()
            if level:
                command += f' {level}'
            else:
                self.call_back('请输入日志等级')
                return
            if self.crashes.isChecked():
                command += ' --ignore-crashes'
            if self.timeouts.isChecked():
                command += ' --ignore-timeouts'
            if self.security_exceptions.isChecked():
                command += ' --ignore-security-exceptions'
            if self.kill_error.isChecked():
                command += ' --kill-process-after-error'
            if self.native_crashes.isChecked():
                command += ' --monitor-native-crashes'
            if self.touch.text():
                command += f' --pct-touch {self.touch.text()}'
            if self.motion.text():
                command += f' --pct-motion {self.motion.text()}'
            if self.pinchzoom.text():
                command += f' --pct-pinchzoom {self.pinchzoom.text()}'
            if self.trackball.text():
                command += f' --pct-trackball {self.trackball.text()}'
            if self.rotation.text():
                command += f' ---pct-rotation {self.rotation.text()}'
            if self.majornav.text():
                command += f' --ptc-majornav {self.majornav.text()}'
            if self.syskeys.text():
                command += f' --ptc-syskeys {self.syskeys.text()}'
            if self.appswitch.text():
                command += f' --pct-appswitch {self.appswitch.text()}'
            event_num = self.event_num.text()
            if event_num:
                command += f' --hprof {event_num}'
            else:
                self.call_back('请输入事件数')
                return
            pid_list = get_adb_pid(device, 'monkey')
            if pid_list:
                self.call_back(f'---------->设备 {product} 正在执行Monkey,请勿重复执行。')
            else:
                cur = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                command += f' 1>{result}/{product}_{cur}_info.txt 2>{result}/{product}_{cur}_error.txt'
                self.call_back(f'---------->Monkey {product} Start')
                self.call_back(command)
                self.thread = AdbThead(cmd=command, mode=4, product=product)
                self.thread.signal.connect(self.call_back)
                self.thread.start()  # 启动线程

        else:
            self.call_back('未选择设备')

    def comboBox_changed(self, product):
        device = self.devices.get(product)
        self.listWidget.clear()
        self.lable_no.clear()
        self.pushButton.setText("日志")
        self.pushButton.setStyleSheet('''
            QPushButton{
                color: rgb(106, 106, 106);
                border-color:rgb(158, 158, 158);
                background-color: white;
            }
            QPushButton:hover{
                color: white;
                background-color: rgb(111, 172, 236);
                border-color:rgb(111, 172, 236);        
            }
        ''')
        if device:
            pid = self.pid.get(device)
            if pid:
                self.pushButton.setText("停止日志")
                self.pushButton.setStyleSheet('''
                    color:white;
                    border-color:red;
                    background-color: red;
                ''')
            self.pushButton_18.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            command = f'adb -s {device} shell pm list package -3'
            self.thread = GetPack(command, self.listWidget)
            self.thread.signal.connect(self.call_back)
            self.thread.start()  # 启动线程

    def listWidget_clicked(self, item):
        self.lineEdit.setText(item.text())
        self.package_apk.setText(item.text())

    # # 重写 关闭事件
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question, self.tr("提示"),
                                      self.tr("确定退出程序\n 还是最小化到系统托盘？"), QtWidgets.QMessageBox.NoButton,
                                      self)
        yr_btn = reply.addButton(self.tr("是的我要退出"), QtWidgets.QMessageBox.YesRole)
        reply.addButton(self.tr("最小化到托盘"), QtWidgets.QMessageBox.NoRole)
        reply.exec_()
        if reply.clickedButton() == yr_btn:
            event.accept()
            self.quit()
            # QApplication.quit()
            # sys.exit(app.exec_())
        else:
            event.ignore()
            # 最小化到托盘
            self.showMinimized()
            self.setWindowFlags(QtCore.Qt.SplashScreen)

    def close_pidd(self):
        pids = reduce(lambda x, y: x.extend(y) or x, [i if isinstance(i, list) else [i] for i in self.pid.values()])
        if platform == 'Darwin':
            p_cmd = "kill -9"
        elif platform == 'Windows':
            p_cmd = "taskkill /F /T /PID"
        for i in pids:
            cmd = f"{p_cmd} {i}"
            run_cmd(cmd)

    def close_adb(self):
        cmd = 'taskkill /f /im adb.exe'
        subprocess.run(cmd)

    def get_product(self):
        product = self.comboBox.currentText()
        device = self.devices.get(product)
        return product, device

    def refresh_dev(self):
        self.product_list = []
        self.comboBox.addItem('获取中...')
        self.comboBox.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        self.mythead = GetDev(self.devices, self.product_list)
        self.mythead.signal.connect(self.call_back)
        self.mythead.start()

    def call_back(self, msg):
        if msg == '100':
            self.pushButton.setText("日志")
            self.pushButton.setStyleSheet('''
                        QPushButton{
                            color: rgb(106, 106, 106);
                            border-color:rgb(158, 158, 158);
                            background-color: white;
                        }
                        QPushButton:hover{
                            color: white;
                            background-color: rgb(111, 172, 236);
                            border-color:rgb(111, 172, 236);        
                        }
                    ''')
        elif msg == '10000':
            self.comboBox.setEnabled(True)
            self.pushButton_3.setEnabled(True)
        elif msg == '2000':
            self.pushButton_18.setEnabled(True)
            self.pushButton_3.setEnabled(True)
            self.pushButton_3.setCursor(QCursor(Qt.PointingHandCursor))
        elif msg == '2001':
            self.listWidget.setHidden(False)
            self.lable_no.setHidden(True)
        elif msg == '2002':
            self.listWidget.setHidden(True)
            self.lable_no.setHidden(False)
            self.lable_no.setText('没有内容')
        elif msg == '00001':
            self.comboBox.setItemText(0, '请选择设备')
            self.comboBox.addItems(self.product_list)
        elif msg == '00002':
            self.comboBox.setItemText(0, '未检测到设备')
        else:
            self.textBrowser.append(msg)
            QApplication.processEvents()

    # 托盘配置
    def tray_config(self):
        self.openAction = QAction("打开", self)
        self.openAction.triggered.connect(self.showNormal)
        self.quitAction = QAction("退出", self)
        self.quitAction.triggered.connect(self.quit)
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.setWindowFlag(Qt.FramelessWindowHint)
        self.trayIconMenu.setAttribute(Qt.WA_TranslucentBackground)
        self.trayIconMenu.setStyleSheet('border-radius: 4px;')
        self.trayIconMenu.addAction(self.openAction)
        self.trayIconMenu.addAction(self.quitAction)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        # self.trayIcon.setIcon(self.icon)
        self.trayIcon.setIcon(QIcon(f"{logo}"))
        self.trayIcon.setToolTip("adb工具")
        self.trayIcon.show()
        self.trayIcon.activated.connect(self.act)

    # 系统托盘左键单机或者双击 显示/隐藏 UI
    def act(self, reason):
        if reason == 3:
            if self.isHidden():
                self.activateWindow()
                self.setWindowFlags(QtCore.Qt.Window)
                self.show()
            else:
                self.hide()

    # 退出
    def quit(self):
        ReadConfig().set_history(self.history)
        ReadConfig().set_phone(str(list(self.queue_phone)))
        self.close_pidd()
        if platform == 'Windows':
            self.close_adb()
        QApplication.quit()

    def init_lineedit(self):
        # 增加自动补全
        self.completer = QCompleter(self.queue_phone)
        # 设置匹配模式 有三种： Qt.MatchStartsWith 开头匹配（默认） Qt.MatchContains 内容匹配 Qt.MatchEndsWith 结尾匹配
        self.completer.setFilterMode(Qt.MatchContains)
        # 设置补全模式 有三种： QCompleter.PopupCompletion（默认） QCompleter.InlineCompletion  QCompleter.UnfilteredPopupCompletion
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        # 给lineedit设置补全器
        self.lineEdit_2.setCompleter(self.completer)

    # def init_combobox(self):
    #     items_list = ['1111', '12312', '123213']
    #     # 增加选项元素
    #     for i in range(len(items_list)):
    #         self.comboBox.addItem(items_list[i])
    #     self.comboBox.setCurrentIndex(-1)
    #
    #     # 增加自动补全
    #     self.completer = QCompleter(items_list)
    #     self.completer.setFilterMode(Qt.MatchContains)
    #     self.completer.setCompletionMode(QCompleter.PopupCompletion)
    #     self.comboBox.setCompleter(self.completer)


# 重写文件推拽
class QEventHandler(QObject):
    def eventFilter(self, obj, event):
        """
        处理窗体内出现的事件，如果有需要则自行添加if判断语句；
        目前已经实现将拖到控件上文件的路径设置为控件的显示文本；
        """
        if event.type() == QEvent.DragEnter:
            event.accept()
        if event.type() == QEvent.Drop:
            md = event.mimeData()
            if md.hasUrls():
                # 此处md.urls()的返回值为拖入文件的file路径列表，即支持多文件同时拖入；
                # 此处默认读取第一个文件的路径进行处理，可按照个人需求进行相应的修改
                url = md.urls()[0]
                obj.setText(url.toLocalFile())
                return True
        return super().eventFilter(obj, event)
