"""
serial_port.py
Author: DdXd
Date: 2025/01/26

加载初始化界面
"""
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QIcon, QTextCursor
from PyQt5.QtWidgets import QComboBox, QMessageBox, QMainWindow

from serialThread import SerialThread
from AutoSend import AutoSend
# 导入设计的ui界面转换成的py文件
import displayUI as Ui_MainWindow

# 最小自动发送的时间间隔
MIN_AUTOSEND_MS = 10


class SerialPort(QMainWindow):
    """
     串口行为
    """

    def __init__(self):
        # QMainWindow构造函数初始化
        super().__init__()

        self.ui = Ui_MainWindow.Ui_Form()
        # 这个函数本身需要传递一个MainWindow类，而该类本身就继承了这个，所以可以直接传入self
        self.ui.setupUi(self)
        self.__init_serial_setting__()
        self.__init_recv_setting__()
        self.__init_recv_data_viewer__()
        self.__init_send_data_viewer__()
        self.__init_auto_send_data__()
        self.__init_auto_line__()

        # 串口接收线程
        self.serial_thread = None
        # 串口自动发送线程
        self.serial_autosend_thread = None

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
        for baud_rate in [1200, 2400, 4800, 9600, 19200, 384000, 57600, 115200, 460800, 921600, 230400, 1500000]:
            self.ui.comboBox_2.addItem(str(baud_rate), baud_rate)
        self.ui.comboBox_2.setCurrentIndex(7)

        # 设置校验位
        self.ui.comboBox_5.setEditable(False)
        self.ui.comboBox_5.setMaxVisibleItems(10)  # 设置最大显示下列项 超过要使用滚动条拖拉
        self.ui.comboBox_5.setInsertPolicy(QComboBox.InsertAfterCurrent)  # 设置插入方式
        for (key, value) in {'None': serial.PARITY_NONE, 'Odd': serial.PARITY_ODD,
                             'Even': serial.PARITY_EVEN, 'Mark': serial.PARITY_MARK,
                             'Space': serial.PARITY_SPACE}.items():
            self.ui.comboBox_5.addItem(key, value)
        # 设置默认值
        self.ui.comboBox_5.setCurrentIndex(0)

        # 初始化数据位列表
        self.ui.comboBox_4.setEditable(False)
        self.ui.comboBox_4.setMaxVisibleItems(10)  # 设置最大显示下列项 超过要使用滚动条拖拉
        self.ui.comboBox_4.setInsertPolicy(QComboBox.InsertAfterCurrent)  # 设置插入方式
        for data_bit in [serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS]:
            self.ui.comboBox_4.addItem(str(data_bit), data_bit)
        # 设置默认值
        self.ui.comboBox_4.setCurrentIndex(3)

        # 初始化停止位列表
        self.ui.comboBox_3.setEditable(False)
        self.ui.comboBox_3.setMaxVisibleItems(10)  # 设置最大显示下列项 超过要使用滚动条拖拉
        self.ui.comboBox_3.setInsertPolicy(QComboBox.InsertAfterCurrent)  # 设置插入方式
        for data_bit in [serial.STOPBITS_ONE, serial.STOPBITS_TWO]:
            self.ui.comboBox_3.addItem(str(data_bit), data_bit)
        # 设置默认值
        self.ui.comboBox_3.setCurrentIndex(0)

        # 初始化周期发送时间(1000ms)
        self.ui.lineEdit_2.setText('1000')

        # 发送新行初始化
        self.ui.checkBox_2.setChecked(True)

        # 打开串口
        self.ui.pushButton_2.clicked.connect(self.open_serial_connection)

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
        if self.ui.radioButton.isChecked():
            self.ui.radioButton_2.setChecked(False)
            if self.serial_thread:
                self.serial_thread.data_format_send = 'hex'

    def rbn_data_format_ascii_clicked(self):
        """
        ascii选项
        :return:
        """
        if self.ui.radioButton_2.isChecked():
            self.ui.radioButton.setChecked(False)
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
        if self.ui.radioButton_3.isChecked():
            self.ui.radioButton_4.setChecked(False)
            if self.serial_thread:
                self.serial_thread.data_format_recv = 'hex'

    def ckb_data_format_ascii_clicked(self):
        """

        :return:
        """
        if self.ui.radioButton_4.isChecked():
            self.ui.radioButton_3.setChecked(False)
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
            self.serial_thread.data_received.connect(self.handle_data_received)
            self.serial_thread.serial_error.connect(self.handler_serial_error)
            self.serial_thread.start()
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
            self.serial_thread.stop()
            # ui界面操作
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

    def handle_data_received(self, data):
        """
        接收数据
        :param data:接收到的数据
        :return:
        """
        # 获取时间
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")

        # 超过5000字符清空
        if len(self.ui.textBrowser.toPlainText()) > 5000:
            self.ui.textBrowser.clear()
        # 更新显示区域中的数据
        if self.ui.checkBox_7.isChecked():
            self.ui.textBrowser.insertPlainText(f"[{current_time}] {data}")
        else:
            self.ui.textBrowser.insertPlainText(f"{data}")

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
        # 发送新行
        if self.ui.checkBox_2.isChecked():
            data += '\r\n'
        # print(data)
        if data != "":
            self.serial_thread.send_data(data)

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
            self.serial_autosend_thread = AutoSend(timelength)
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
        if self.ui.checkBox_2.isChecked():
            self.serial_thread.auto_line = True
        else:
            self.serial_thread.auto_line = False
