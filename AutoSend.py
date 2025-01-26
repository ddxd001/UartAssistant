from PyQt5.QtCore import *
import time


class AutoSend(QThread):
    timeout = pyqtSignal(bool)

    def __init__(self, timelength):
        super().__init__()
        self.__timelength = timelength
        self.__running = False

    def run(self):
        if self.__running:
            return
        self.__running = True
        while self.__running:
            time.sleep(self.__timelength * 0.001)  # 毫秒(ms)
            self.timeout.emit(True)

    @property
    def isRunning(self):
        return self.__running

    @isRunning.setter
    def isRunning(self, value):
        if type(value) is not bool:
            raise TypeError
        self.__running = value

    def stop(self):
        self.__running = False
        self.wait()
