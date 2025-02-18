"""
project:    UartAssistant
branch:     master
author:     DdXd
date:       2025/01/24
python:     3.8
"""
import sys
from serial_port import SerialPort
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    # 先建立一个app
    app = QApplication(sys.argv)
    # 初始化一个对象，调用init函数，已加载设计的ui文件
    ui = SerialPort()
    # 显示这个ui
    ui.show()
    # 运行界面，响应按钮等操作
    sys.exit(app.exec_())
