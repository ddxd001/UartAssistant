"""
serial_port.py
Author: DdXd
Date: 2025/01/26

加载初始化界面
主线程，负责渲染窗口界面，接收界面操作功能
"""
import json
import os
import sys
import webbrowser
from datetime import datetime

import serial
import serial.tools.list_ports
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QTextCursor, QIcon
from PyQt5.QtWidgets import *

import settings_thread
from serialThread import SerialThread
from timeClock import timeClock
from settings_thread import SettingsThread
# 导入设计的ui界面转换成的py文件
import displayUI as Ui_MainWindow
from QSSLoader import QSSLoader

# 最小自动发送的时间间隔
MIN_AUTOSEND_MS = 10
SHORTCUT_LIST_NUM = 60
BASE_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
AUTO_REFRESH_INTERVAL = 800


class SerialPort(QMainWindow):
    """
     串口行为
    """

    def __init__(self):
        # QMainWindow构造函数初始化
        super().__init__()

        # 串口接收线程
        self.serial_thread = None
        # 串口自动发送线程
        self.serial_autosend_thread = None
        self.settingsMenu = None
        self.autosave_timer = None
        self.serial_port_item = None

        self.ui = Ui_MainWindow.Ui_MainWindow()
        # 这个函数本身需要传递一个MainWindow类，而该类本身就继承了这个，所以可以直接传入self
        self.ui.setupUi(self)
        self.__init_serial_setting__()
        self.__init_recv_setting__()
        self.__init_recv_data_viewer__()
        self.__init_send_data_viewer__()
        self.__init_auto_send_data__()
        self.__init_auto_line__()
        self.__init_shortcut__(SHORTCUT_LIST_NUM)
        self.__init_menu__()
        self.__init_shortcut_autosave__()
        self.__init_sendFile__()
        self.__init_autosave__()
        self.__init_autoRefresh__()
        self.__init_switch_theme__()

        # 设置logo
        self.setWindowIcon(QIcon(os.path.join(BASE_PATH, 'logo.ico')))

    def __del__(self):
        self.__del_shortcut_autosave__()
        self.handler_autosave()

    def closeEvent(self, event):
        self.__del__()
        event.accept()

    def __init_switch_theme__(self):
        self.ui.actiondefault.triggered.connect(lambda: self.switch_theme('default'))
        self.ui.actionlight.triggered.connect(lambda: self.switch_theme('light'))
        self.ui.actiondark.triggered.connect(lambda: self.switch_theme('dark'))

    def switch_theme(self, theme_name):
        with open(os.path.join(BASE_PATH, 'style/' + theme_name + '.qss'), 'r', encoding='utf-8') as f:
            qss_sheet = f.read()
        self.setStyleSheet(qss_sheet)

    def __init_serial_setting__(self):
        """
        配置界面选项
        :return:
        """
        # 串口列表
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            self.ui.comboBox.addItem(port[0])

        # 设置波特率
        for baud_rate in [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 460800, 921600, 230400, 1500000]:
            self.ui.comboBox_2.addItem(str(baud_rate), baud_rate)

        # 设置校验位
        self.ui.comboBox_5.setEditable(False)
        self.ui.comboBox_5.setMaxVisibleItems(10)  # 设置最大显示下列项 超过要使用滚动条拖拉
        self.ui.comboBox_5.setInsertPolicy(QComboBox.InsertAfterCurrent)  # 设置插入方式
        for (key, value) in {'None': serial.PARITY_NONE, 'Odd': serial.PARITY_ODD,
                             'Even': serial.PARITY_EVEN, 'Mark': serial.PARITY_MARK,
                             'Space': serial.PARITY_SPACE}.items():
            self.ui.comboBox_5.addItem(key, value)

        # 初始化数据位列表
        self.ui.comboBox_4.setEditable(False)
        self.ui.comboBox_4.setMaxVisibleItems(10)  # 设置最大显示下列项 超过要使用滚动条拖拉
        self.ui.comboBox_4.setInsertPolicy(QComboBox.InsertAfterCurrent)  # 设置插入方式
        for data_bit in [serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS]:
            self.ui.comboBox_4.addItem(str(data_bit), data_bit)

        # 初始化停止位列表
        self.ui.comboBox_3.setEditable(False)
        self.ui.comboBox_3.setMaxVisibleItems(10)  # 设置最大显示下列项 超过要使用滚动条拖拉
        self.ui.comboBox_3.setInsertPolicy(QComboBox.InsertAfterCurrent)  # 设置插入方式
        for data_bit in [serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO]:
            self.ui.comboBox_3.addItem(str(data_bit), data_bit)

        # radiobutton组 # 解决点击已选择radiobutton时取消选择bug
        self.ui.ButtonGroup_1 = QButtonGroup()
        self.ui.ButtonGroup_2 = QButtonGroup()
        self.ui.ButtonGroup_1.addButton(self.ui.radioButton)
        self.ui.ButtonGroup_1.addButton(self.ui.radioButton_2)
        self.ui.ButtonGroup_2.addButton(self.ui.radioButton_3)
        self.ui.ButtonGroup_2.addButton(self.ui.radioButton_4)

        self.make_settings()

        # 打开串口
        self.ui.pushButton_2.clicked.connect(self.open_serial_connection)

    def set_default_settings(self):
        self.ui.comboBox_2.setCurrentIndex(7)
        self.ui.comboBox_5.setCurrentIndex(0)
        self.ui.comboBox_4.setCurrentIndex(3)
        self.ui.comboBox_3.setCurrentIndex(0)
        self.ui.lineEdit_2.setText('1000')
        self.ui.checkBox_2.setChecked(True)

    def make_settings(self):
        try:
            with open(os.path.join(BASE_PATH, 'settings.json'), 'r', encoding='utf-8') as infile:
                settings_dict = json.load(infile)
            # 接收显示
            if settings_dict['comboBox_3'] == 0:
                self.ui.radioButton_3.setChecked(False)
                self.ui.radioButton_4.setChecked(True)
            else:
                self.ui.radioButton_3.setChecked(True)
                self.ui.radioButton_4.setChecked(False)
            # 发送编码
            if settings_dict['comboBox_4'] == 0:
                self.ui.radioButton.setChecked(False)
                self.ui.radioButton_2.setChecked(True)
                self.rbn_data_format_ascii_clicked()
            else:
                self.ui.radioButton.setChecked(True)
                self.ui.radioButton_2.setChecked(False)
                self.rbn_data_format_hex_clicked()
            # 波特率设置
            self.ui.comboBox_2.setCurrentIndex(settings_dict['comboBox_5'])
            # 数据位设置
            self.ui.comboBox_4.setCurrentIndex(settings_dict['comboBox_6'])
            # 校验位设置
            self.ui.comboBox_5.setCurrentIndex(settings_dict['comboBox_7'])
            # 停止位设置
            self.ui.comboBox_3.setCurrentIndex(settings_dict['comboBox_8'])
            # 时间戳
            self.ui.checkBox_7.setChecked(settings_dict['checkBox'])
            # 输出显示
            self.ui.checkBox.setChecked(settings_dict['checkBox_2'])
            # 自动保存
            self.ui.checkBox_6.setChecked(settings_dict['checkBox_3'])
            # 发送新行
            self.ui.checkBox_2.setChecked(settings_dict['checkBox_4'])
            # 设置主题
            if settings_dict['comboBox_9'] == 0:
                self.switch_theme('default')
            elif settings_dict['comboBox_9'] == 1:
                self.switch_theme('light')
            elif settings_dict['comboBox_9'] == 2:
                self.switch_theme('dark')
            self.handler_auto_line_data()
            # 设置字体

        except FileNotFoundError:
            self.set_default_settings()

    def __init_recv_setting__(self):
        """
        接收初始化设置
        :return:
        """
        self.ui.radioButton.clicked.connect(self.rbn_data_format_hex_clicked)
        self.ui.radioButton_2.clicked.connect(self.rbn_data_format_ascii_clicked)

    def rbn_data_format_hex_clicked(self):
        """
        16进制选项
        :return:
        """
        if self.serial_thread:
            self.serial_thread.data_format_send = 'hex'

    def rbn_data_format_ascii_clicked(self):
        """
        ascii选项
        :return:
        """
        if self.serial_thread:
            self.serial_thread.data_format_send = 'ascii'

    def __init_recv_data_viewer__(self):
        """
        初始化串口数据接收区
        :return:
        """
        # 设置为只读且每次自动滚动到后一行
        self.ui.textBrowser.setReadOnly(True)
        self.ui.textBrowser.textChanged.connect(
            lambda: self.ui.textBrowser.moveCursor(QTextCursor.End)
        )
        self.ui.radioButton_3.clicked.connect(self.ckb_data_format_hex_clicked)
        self.ui.radioButton_4.clicked.connect(self.ckb_data_format_ascii_clicked)

    def ckb_data_format_hex_clicked(self):
        """

        :return:
        """
        if self.serial_thread:
            self.serial_thread.data_format_recv = 'hex'

    def ckb_data_format_ascii_clicked(self):
        """

        :return:
        """
        if self.serial_thread:
            self.serial_thread.data_format_recv = 'ascii'

    def __init_send_data_viewer__(self):
        """
        初始化串口数据发送区域
        :return:
        """
        self.ui.pushButton.clicked.connect(self.send_serial_data)
        self.ui.pushButton_3.clicked.connect(self.clear_serial_data)

    def open_serial_connection(self):
        """
        打开串口
        :return:
        """
        if not self.serial_thread or not self.serial_thread.isRunning():
            # 参数校验__validate_setting__
            if not self.__validata_setting__():
                return

            # 建立一个串口
            self.serial_thread = SerialThread(
                self.ui.comboBox.currentText(),  # 端口
                self.ui.comboBox_2.currentData(),  # 波特率
                self.ui.comboBox_4.currentData(),  # 数据位
                self.ui.comboBox_5.currentData(),  # 校验位
                self.ui.comboBox_3.currentData(),  # 停止位
                'hex' if self.ui.radioButton.isChecked() else 'ascii',
                'hex' if self.ui.radioButton_3.isChecked() else 'ascii',
                self.ui.checkBox_2.isChecked()
            )
            # 串口线程操作
            self.serial_thread.data_received.connect(
                lambda data_received: self.handle_data_display(
                    data_received,
                    "recv as " + ('hex' if self.ui.radioButton_3.isChecked() else 'asc')
                )
            )
            # 数据解析操作
            self.serial_thread.data_received.connect(
                lambda data_received: self.data_analysis(data_received)
            )
            self.serial_thread.serial_error.connect(self.handler_serial_error)
            self.serial_thread.start()
            self.auto_save_timer_thread()  # 重新加载自动保存
            # ui界面操作
            self.ui.comboBox.setEnabled(False)
            self.ui.comboBox_2.setEnabled(False)
            self.ui.comboBox_3.setEnabled(False)
            self.ui.comboBox_4.setEnabled(False)
            self.ui.comboBox_5.setEnabled(False)
            self.ui.pushButton.setEnabled(True)
            self.ui.pushButton_3.setEnabled(True)
            self.ui.checkBox_8.setEnabled(True)
            self.ui.label_8.setEnabled(True)
            self.ui.lineEdit_2.setEnabled(True)
            self.ui.pushButton_2.setText("关闭串口")
        else:
            # 串口线程操作
            if self.serial_autosend_thread:
                self.serial_autosend_thread.stop()  # 防止在自动发送时关闭串口导致连续弹窗问题
            if self.autosave_timer:
                self.autosave_timer.stop()
            self.serial_thread.stop()
            # ui界面操作
            self.ui.checkBox_8.setChecked(False)
            self.ui.comboBox.setEnabled(True)
            self.ui.comboBox_2.setEnabled(True)
            self.ui.comboBox_3.setEnabled(True)
            self.ui.comboBox_4.setEnabled(True)
            self.ui.comboBox_5.setEnabled(True)
            self.ui.pushButton.setEnabled(False)
            self.ui.pushButton_3.setEnabled(False)
            self.ui.checkBox_8.setEnabled(False)
            self.ui.label_8.setEnabled(False)
            self.ui.lineEdit_2.setEnabled(False)
            self.ui.pushButton_2.setText("打开串口")

    def __validata_setting__(self):
        """
        校验串口设置参数
        :return:
        """
        # 参数校验
        if self.ui.comboBox.currentIndex() == -1:
            QMessageBox.warning(self, "Warning", "请选择串口！")
            return False
        if self.ui.comboBox_2.currentIndex() == -1:
            QMessageBox.warning(self, "Warning", "请选择波特率！")
            return False
        if self.ui.comboBox_5.currentIndex() == -1:
            QMessageBox.warning(self, "Warning", "请选择校验位！")
            return False
        if self.ui.comboBox_4.currentIndex() == -1:
            QMessageBox.warning(self, "Warning", "请选择数据位！")
            return False
        if self.ui.comboBox_3.currentIndex() == -1:
            QMessageBox.warning(self, "Warning", "请选择停止位！")
            return False

        return True

    def handler_serial_error(self, error):
        """
        串口接收线程异常
        :param error:
        :return:
        """
        QMessageBox.critical(self, '错误', error)

    def handle_data_display(self, data, data_from: str):
        """
        将数据显示到textBrowser
        :param data_from: 数据来源（send/recv）
        :param data:接收到的数据
        :return:
        """
        # 获取时间
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        display_str = ""
        # 超过5000字符清空
        if len(self.ui.textBrowser.toPlainText()) > 5000:
            self.ui.textBrowser.clear()
        # 更新显示区域中的数据
        if self.ui.checkBox.isChecked():  # 输出显示
            display_str += f"[{data_from}]"
        if self.ui.checkBox_7.isChecked():  # 时间戳
            display_str += f"[{current_time}]"
        display_str += f"{data}"
        self.ui.textBrowser.insertPlainText(display_str)

        # 必须是hex格式
        if self.ui.radioButton_2.isChecked():
            return

    def send_serial_data(self):
        """
        发送数据
        :return:
        """
        if not self.serial_thread or not self.serial_thread.isRunning():
            QMessageBox.warning(self, "Warning", "请先打开串口！")
            return
        data = self.ui.textEdit.toPlainText()
        # print(data)
        if data != "":
            self.serial_thread.send_data(data)
            if self.ui.checkBox.isChecked():  # 打开显示输出
                self.handle_data_display(data + "\r\n",
                                         "send as " + ('hex' if self.ui.radioButton.isChecked() else 'asc'))

    def clear_serial_data(self):
        """
        清除数据发送区
        :return:
        """
        self.ui.textEdit.clear()

    def __init_auto_send_data__(self):
        """
        周期发送初始化
        :return:
        """
        # 慎用checkBox.stateChanged.connect
        self.ui.checkBox_8.clicked.connect(self.handler_auto_send_data)

    def handler_auto_send_data(self):
        """
        创建`serial_autosend_thread`线程每隔`timelength`返回一个True信号
        :return:
        """
        if self.ui.checkBox_8.isChecked():
            timelength = self.ui.lineEdit_2.text()
            if timelength == '':
                QMessageBox.warning(self, "warning", "设置周期时间！")
                self.ui.checkBox_8.setChecked(False)
                return
            try:
                timelength = int(timelength)
            except ValueError as e:
                QMessageBox.warning(self, "warning", str(e))
                self.ui.checkBox_8.setChecked(False)
                return
            if timelength < MIN_AUTOSEND_MS:
                QMessageBox.warning(self, "warning", "周期时间太短！")
                self.ui.checkBox_8.setChecked(False)
                return
            self.serial_autosend_thread = timeClock(timelength)
            self.serial_autosend_thread.timeout.connect(self.send_serial_data)
            self.serial_autosend_thread.start()
        else:
            if self.serial_autosend_thread and self.serial_autosend_thread.isRunning:
                self.serial_autosend_thread.stop()

    def __init_auto_line__(self):
        self.ui.checkBox_2.clicked.connect(self.handler_auto_line_data)

    def handler_auto_line_data(self):
        if not self.serial_thread or not self.serial_thread.isRunning():
            return
        self.serial_thread.auto_line = self.ui.checkBox_2.isChecked()

    def __init_shortcut__(self, nums: int):
        """
        批量初始化快捷发送功能
        :param nums: 快捷指令数量
        :return:
        """
        for i in range(1, nums + 1):
            self.child_button = self.ui.scrollArea.findChild(QPushButton, 'pb_{}'.format(i))
            self.child_button.clicked.connect(self.handler_shortcut)

    def handler_shortcut(self):
        """
        快捷发送对应lineEdit内容
        :return:
        """
        if not self.serial_thread or not self.serial_thread.isRunning():
            QMessageBox.warning(self, 'warning', '未打开串口')
            return
        sent = self.sender().text()
        child_lineEdit = self.ui.scrollArea.findChild(QLineEdit, 'le_{}'.format(sent))

        # 通过ascii发送
        self.ui.radioButton_2.setChecked(True)
        self.serial_thread.data_format_send = 'ascii'

        try:
            data = child_lineEdit.text()
            self.serial_thread.send_data(data)
            if self.ui.checkBox.isChecked():  # 打开显示输出
                self.handle_data_display(data + "\r\n",
                                         "send as " + ('hex' if self.ui.radioButton.isChecked() else 'asc'))
        except Exception as e:
            QMessageBox.warning(self, 'warning', str(e))

    def __init_menu__(self):
        """
        顶部菜单初始化
        :return:
        """
        # 保存文件
        self.ui.action_4.triggered.connect(self.handler_saveFile)
        self.ui.action_3.triggered.connect(self.handler_help)
        self.ui.action_6.triggered.connect(self.handler_exportShortcut)
        self.ui.action_5.triggered.connect(self.handler_importShortcut)
        self.ui.actions.triggered.connect(self.handler_settings)
        self.ui.action_7.triggered.connect(self.handler_shortcutCleanup)
        self.ui.actionabout_UartAssistant_v1_0.triggered.connect(self.handler_aboutUartAssistant)
        self.ui.action_8.triggered.connect(self.handler_cleanup_recv)

    @staticmethod
    def handler_help(self):
        file_path = os.path.join(BASE_PATH, 'html/UartAssistant使用帮助.html')
        url = 'file://' + file_path
        webbrowser.open(url)

    @staticmethod
    def handler_aboutUartAssistant(self):
        file_path = os.path.join(BASE_PATH, 'html/README.html')
        url = 'file://' + file_path
        webbrowser.open(url)

    def handler_cleanup_recv(self):
        self.ui.textBrowser.clear()

    def handler_saveFile(self):
        """
        顶部菜单保存
        :return:
        """
        text = self.ui.textBrowser.toPlainText()
        if text == '':
            QMessageBox.warning(self, 'empty file', 'nothing to save')
            return
        save_path = QFileDialog.getSaveFileName(self, "设置路径", "./", "Text Files (*.txt)")
        if save_path[0] == '':
            return
        file = open(save_path[0], 'w')
        file.write(text)

    def handler_exportShortcut(self):
        """
        导出快捷发送中的内容到文件（*.）中
        :return:
        """
        exportStr = ''
        for i in range(1, SHORTCUT_LIST_NUM + 1):
            tmp = eval(f'self.ui.le_{i}.text()')
            tmp = tmp.strip()
            if tmp != '':
                exportStr += str(i) + ' ' + tmp + '\n'
        if exportStr != '':
            save_path = QFileDialog.getSaveFileName(self, "设置路径", "./", "Text Files (*.dat)")
            if save_path[0] == '':
                return
            file = open(save_path[0], 'w')
            file.write(exportStr)

    def handler_importShortcut(self):
        """
        将一定格式的文件导入到快捷发送中
        :return:
        """
        file_path = QFileDialog.getOpenFileName(self, "选择文件", "./", "Text Files (*.dat)")
        if file_path[0] == '':
            return
        with open(file_path[0], 'r') as file:
            line = file.readline()
            line = line.strip()
            while line:
                data = line.split(' ', 1)
                print(data[0])
                try:
                    child_lineEdit = eval('self.ui.le_{}'.format(data[0]))
                    child_lineEdit.setText(data[1].strip())
                except Exception as e:
                    QMessageBox.warning(self, 'warning', str(e))
                    return
                line = file.readline()

    def handler_settings(self):
        self.settingsMenu = SettingsThread()
        self.settingsMenu.show()
        self.settingsMenu.setting_data.connect(self.make_settings)
        self.settingsMenu.setting_error.connect(self.make_settings_err)

    def make_settings_err(self):
        QMessageBox.warning(self, 'warning', '初始化设置失败')

    def __init_shortcut_autosave__(self):
        """
        加载上次关闭时快捷发送内容
        :return:
        """
        file_path = os.path.join(BASE_PATH, 'shortcut_autosave.dat')
        with open(file_path, 'r') as file:
            line = file.readline()
            line = line.strip()
            while line:
                data = line.split(' ', 1)
                try:
                    child_lineEdit = eval('self.ui.le_{}'.format(data[0]))
                    child_lineEdit.setText(data[1].strip())
                except Exception as e:
                    print(str(e))
                line = file.readline()

    def __del_shortcut_autosave__(self):
        """
        关闭窗口时调用该函数保存快捷发送内容，在下次打开程序后加载
        :return:
        """
        exportStr = ''
        for i in range(1, SHORTCUT_LIST_NUM + 1):
            tmp = eval(f'self.ui.le_{i}.text()')
            tmp = tmp.strip()
            if tmp != '':
                exportStr += str(i) + ' ' + tmp + '\n'

        self.file_path = os.path.join(BASE_PATH, 'shortcut_autosave.dat')
        with open(self.file_path, 'w') as file:
            file.write(exportStr)

    def handler_shortcutCleanup(self):
        for i in range(1, SHORTCUT_LIST_NUM + 1):
            chile_lineEdit = eval('self.ui.le_{}'.format(i))
            chile_lineEdit.clear()

    def __init_sendFile__(self):
        self.ui.toolButton.clicked.connect(self.handler_selectFile)
        self.ui.pushButton_4.clicked.connect(self.handler_confirmSelect)
        self.ui.pushButton_5.clicked.connect(self.handler_send_file)

    def handler_selectFile(self):
        file_path = QFileDialog.getOpenFileName(self, "选择文件", "./")
        if file_path[0] == '':
            return
        self.ui.lineEdit.setText(file_path[0])

    def handler_confirmSelect(self):
        file_path = self.ui.lineEdit.text()
        if file_path == '':
            QMessageBox.warning(self, '未选择文件', '请先选择文件')
            return
        try:
            with open(file_path, 'r') as file:
                exportStr = file.read()
                self.ui.textBrowser_2.setText(exportStr)
        except Exception as e:
            QMessageBox.warning(self, '文件打开失败', str(e))
            self.ui.textBrowser_2.clear()

    def handler_send_file(self):
        if not self.serial_thread or not self.serial_thread.isRunning():
            QMessageBox.warning(self, "Warning", "请先打开串口！")
            return
        self.ui.radioButton_2.setChecked(True)
        self.serial_thread.data_format_send = 'ascii'
        self.ui.checkBox_2.setChecked(True)
        data = self.ui.textBrowser_2.toPlainText()
        if data == '':
            return
        self.serial_thread.send_data(data)
        if self.ui.checkBox.isChecked():  # 打开显示输出
            self.handle_data_display(data + "\r\n",
                                     "send as " + ('hex' if self.ui.radioButton.isChecked() else 'asc'))

    def __init_autosave__(self):
        self.ui.checkBox_6.clicked.connect(self.auto_save_timer_thread)

    def handler_autosave(self):
        """
        自动保存
        :return:
        """
        if self.ui.checkBox_6.isChecked():
            date = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            data = self.ui.textBrowser.toPlainText()
            with open(os.path.join(BASE_PATH, 'settings.json'), 'r') as file:
                jsonDir = file.read()
                jsonDir = json.loads(jsonDir)
                file_path = jsonDir['lineEdit']
                print(file_path)
                if file_path == '':
                    file_path = BASE_PATH
            try:
                with open(os.path.join(file_path, f'{date}_autosave.txt'), 'w') as file:
                    file.write(data)
            except Exception as e:
                QMessageBox.warning(self, 'warning', str(e))

    def auto_save_timer_thread(self):
        if not self.serial_thread or not self.serial_thread.isRunning():
            return
        if self.ui.checkBox_6.isChecked():
            with open(os.path.join(BASE_PATH, 'settings.json'), 'r') as file:
                jsonDir = file.read()
                jsonDir = json.loads(jsonDir)
                if jsonDir['checkBox_5'] and (not self.autosave_timer or not self.autosave_timer.isRunning):
                    self.autosave_timer = timeClock(1000 * int(jsonDir['lineEdit_2']))
                    self.autosave_timer.start()
                    self.autosave_timer.timeout.connect(self.handler_autosave)
                else:
                    if self.autosave_timer and self.autosave_timer.isRunning:
                        self.autosave_timer.stop()
        else:
            if self.autosave_timer and self.autosave_timer.isRunning:
                self.autosave_timer.stop()

    def __init_autoRefresh__(self, ):
        """
        自动刷新串口列表
        AUTO_REFRESH_INTERVAL:刷新间隔时间
        :return:
        """
        self.autoRefresh_timer = timeClock(AUTO_REFRESH_INTERVAL)
        self.autoRefresh_timer.start()
        self.autoRefresh_timer.timeout.connect(self.handler_autoRefresh)

    def handler_autoRefresh(self):
        if self.serial_thread and self.autoRefresh_timer.isRunning:
            return
        ports = list(serial.tools.list_ports.comports())
        if ports == self.serial_port_item:
            return
        self.serial_port_item = ports
        self.ui.comboBox.clear()
        for port in ports:
            self.ui.comboBox.addItem(port[0])

    def data_analysis(self, data_received):
        if self.ui.checkBox_3.isChecked():
            try:
                data_head = self.ui.lineEdit_3.text()
                data_head = int(data_head, 16)
                data_tail = self.ui.lineEdit_4.text()
                data_tail = int(data_tail, 16)
            except Exception as e:
                QMessageBox.warning(self, 'warning', str(e))
            send_list = []
            while data_received != '':
                try:
                    num = int(data_received[0:2], 16)
                except ValueError:
                    return
                data_received = data_received[2:].strip()
                send_list.append(num)
            if send_list[0] == data_head and send_list[len(send_list) - 1] == data_tail:
                del send_list[0]
                del send_list[-1]
                print(send_list)
                self.ui.textBrowser_3.insertPlainText('[package]:' + self.deep_analysis(send_list) + '\n')
        else:
            return

    def deep_analysis(self, ana_list):
        """
         定制化分析，收到必须是偶数个数，将两个八位二进制数合成十六位二进制并返回十进制
         :param ana_list: 分析数组
         :return: 分析结果：一个十进制数
        """
        if len(ana_list) == 0:
            return '<no data>'
        if len(ana_list) % 2 != 0:
            return '<odd data>'
        ret_list = []
        for i in range(0, len(ana_list), 2):
            data = ana_list[i] << 8 | ana_list[i + 1]
            ret_list.append(data)
        return str(ret_list)
