"""
settings_thread.py
设置窗口
"""
import os
import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import Settings
import json

FONT_LIST = ["Arial Unicode MS", "Fixedsys", "SimSun-ExtB", "System", "Terminal", "仿宋", "华文中宋", "华文仿宋",
             "华文宋体", "华文彩云", "华文新魏", "华文楷体", "华文琥珀", "华文细黑", "华文行楷", "华文隶书", "宋体",
             "幼圆", "微软雅黑", "新宋体", "方正姚体", "方正舒体", "楷体", "隶书", "黑体", ]
BASE_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
MIN_AUTOSAVE_TIME = 5


class SettingsThread(QMainWindow):
    setting_data = pyqtSignal(bool)
    setting_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.ui = Settings.Ui_MainWindow()
        self.ui.setupUi(self)
        self.__init_ui__()
        self.__init_buttons__()
        self.load_settings()

    def __del__(self):
        pass

    def closeEvent(self, event):
        self.__del__()
        event.accept()

    def __init_ui__(self):
        # 字体设置
        for font in FONT_LIST:
            self.ui.comboBox.addItem(font, font)
        # 字体大小
        for size in [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]:
            self.ui.comboBox_2.addItem(str(size), str(size))
        # 主题
        for theme in ['default', 'light', 'dark']:
            self.ui.comboBox_9.addItem(theme, theme)
        # 接收显示、发送编码
        for choice in ['ASCII', 'HEX']:
            self.ui.comboBox_3.addItem(choice, choice)
            self.ui.comboBox_4.addItem(choice, choice)
        # 波特率
        for baud_rate in [1200, 2400, 4800, 9600, 19200, 384000, 57600, 115200, 460800, 921600, 230400, 1500000]:
            self.ui.comboBox_5.addItem(str(baud_rate), str(baud_rate))
        # 设置校验位
        self.ui.comboBox_7.setMaxVisibleItems(10)  # 设置最大显示下列项 超过要使用滚动条拖拉
        self.ui.comboBox_7.setInsertPolicy(QComboBox.InsertAfterCurrent)  # 设置插入方式
        for key in ['None', 'Odd', 'Even', 'Mark', 'Space']:
            self.ui.comboBox_7.addItem(key, key)
        # 初始化数据位列表
        self.ui.comboBox_6.setEditable(False)
        self.ui.comboBox_6.setMaxVisibleItems(10)  # 设置最大显示下列项 超过要使用滚动条拖拉
        self.ui.comboBox_6.setInsertPolicy(QComboBox.InsertAfterCurrent)  # 设置插入方式
        for data_bit in [5, 6, 7, 8]:
            self.ui.comboBox_6.addItem(str(data_bit), data_bit)
        # 初始化停止位列表
        self.ui.comboBox_8.setEditable(False)
        self.ui.comboBox_8.setMaxVisibleItems(10)  # 设置最大显示下列项 超过要使用滚动条拖拉
        self.ui.comboBox_8.setInsertPolicy(QComboBox.InsertAfterCurrent)  # 设置插入方式
        for data_bit in [1, 1.5, 2]:
            self.ui.comboBox_8.addItem(str(data_bit), data_bit)
        self.handler_setDefault()

    def export_settings(self):
        # comboBox
        json_dict = {}
        set_list = self.findChildren(QComboBox)
        for child in set_list:
            json_dict[child.objectName()] = child.currentIndex()
        set_list = self.findChildren(QLineEdit)
        for child in set_list:
            json_dict[child.objectName()] = child.text()
        set_list = self.findChildren(QCheckBox)
        for child in set_list:
            json_dict[child.objectName()] = child.isChecked()
        json_str = json.dumps(json_dict)
        try:
            with open(os.path.join(BASE_PATH, 'settings.json'), 'w') as outfile:
                outfile.write(json_str)
        except Exception as err:
            self.setting_error.emit(str(err))

    def load_settings(self):
        try:
            with open(os.path.join(BASE_PATH, 'settings.json'), 'r') as infile:
                json_str = infile.read()
            json_dict = json.loads(json_str)
            for obj, index in json_dict.items():
                if self.findChild(QComboBox, obj):
                    self.findChild(QComboBox, obj).setCurrentIndex(index)
                elif self.findChild(QLineEdit, obj):
                    self.findChild(QLineEdit, obj).setText(str(index))
                elif self.findChild(QCheckBox, obj):
                    self.findChild(QCheckBox, obj).setChecked(index)
            if self.ui.checkBox_5.isChecked():
                self.ui.lineEdit_2.setEnabled(True)
        except Exception as err:
            self.setting_error.emit(str(err))

    def __init_buttons__(self):
        self.ui.pushButton.clicked.connect(self.handler_setDefault)
        self.ui.pushButton_3.clicked.connect(self.handler_apply)
        self.ui.pushButton_4.clicked.connect(self.handler_cancel)
        self.ui.pushButton_5.clicked.connect(self.handler_commit)
        self.ui.toolButton.clicked.connect(self.handler_setPath)
        self.ui.checkBox_5.clicked.connect(self.handler_autosave)

    def handler_autosave(self):
        if self.ui.checkBox_5.isChecked():
            self.ui.lineEdit_2.setEnabled(True)
        else:
            self.ui.lineEdit_2.setEnabled(False)

    def handler_setPath(self):
        file_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if file_path == '':
            return
        self.ui.lineEdit.setText(file_path)

    def handler_setDefault(self):
        self.ui.comboBox.setCurrentIndex(0)
        self.ui.comboBox_2.setCurrentIndex(3)
        self.ui.comboBox_3.setCurrentIndex(1)
        self.ui.comboBox_4.setCurrentIndex(1)
        self.ui.comboBox_5.setCurrentIndex(7)
        self.ui.comboBox_7.setCurrentIndex(0)
        self.ui.comboBox_6.setCurrentIndex(3)
        self.ui.comboBox_8.setCurrentIndex(0)
        self.ui.lineEdit_3.setText('1000')
        self.ui.checkBox.setChecked(True)
        self.ui.checkBox_4.setChecked(True)
        self.ui.checkBox_2.setChecked(False)
        self.ui.checkBox_3.setChecked(False)
        self.ui.lineEdit.clear()
        self.ui.lineEdit_2.clear()
        self.ui.lineEdit_2.setEnabled(False)

    def handler_apply(self):
        if self.ui.checkBox.isChecked():
            tim = self.ui.lineEdit_2.text()
            try:
                tim = int(tim)
                if tim < MIN_AUTOSAVE_TIME:
                    QMessageBox.warning(self, '间隔时间过短', '时间太短')
                    self.ui.lineEdit_2.clear()
                    return
            except ValueError as e:
                QMessageBox.warning(self, 'not a number', str(e))
                self.ui.lineEdit_2.clear()
                return
        self.export_settings()
        self.setting_data.emit(True)

    def handler_cancel(self):
        self.load_settings()

    def handler_commit(self):
        self.handler_apply()
        self.close()
