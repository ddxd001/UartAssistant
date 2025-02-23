"""
串口线程创建，串口操作
串口线程，在打开串口时创建线程，包含串口相关的操作
Pyqt5 QThread多线程操作参考链接：https://www.cnblogs.com/linyfeng/p/12239856.html
"""
from PyQt5.QtCore import *
import serial


class SerialThread(QThread):
    """
    创建一个继承自QThread的SerialThread类，实现串口数据的读取/发送
    """
    data_received = pyqtSignal(str)
    serial_error = pyqtSignal(str)

    def __init__(self, port, baud_rate, data_bits, parity_bits, stop_bits, data_format_send, data_format_recv, auto_line):
        """
        初始化
        :param port:            串口号
        :param baud_rate:       波特率
        :param data_bits:       数据位
        :param parity_bits:     校验位
        :param stop_bits:       停止位
        :param data_format_send:发送数据格式
        :param data_format_recv:接收数据格式
        """
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.data_bits = data_bits
        self.parity_bits = parity_bits
        self.stop_bits = stop_bits

        # 串口运行标志位
        self.running = False
        # 串口
        self.serial = None
        # 数据格式
        self.__data_format_send = data_format_send
        self.__data_format_recv = data_format_recv
        # 开启自动追加换行
        self.__auto_line = auto_line

    # 通过@property将data_format_send(data_format_recv)修饰为属性
    @property
    def data_format_send(self):
        """
        把一个getter方法变成属性
        :param self:
        :return:
        """
        return self.__data_format_send

    @data_format_send.setter
    def data_format_send(self, value):
        if not isinstance(value, str):
            raise TypeError('data_format must be str')
        if value not in ['hex', 'ascii']:
            raise ValueError('data_format must be either hex or ascii')
        self.__data_format_send = value

    @property
    def data_format_recv(self):
        """

        :return:
        """
        return self.__data_format_recv

    @data_format_recv.setter
    def data_format_recv(self, value):
        if not isinstance(value, str):
            raise TypeError('data_format must be str')
        if value not in ['hex', 'ascii']:
            raise ValueError('data_format must be either hex or ascii')
        self.__data_format_recv = value

    @property
    def auto_line(self):
        return self.__auto_line

    @auto_line.setter
    def auto_line(self, value):
        if not isinstance(value, bool):
            raise TypeError('auto_line must be bool')
        self.__auto_line = value

    # 重写run（）在执行serial_thread.start()时执行
    def run(self):
        if self.running:
            return

        try:
            with serial.Serial(
                    port=self.port,
                    baudrate=self.baud_rate,
                    parity=self.parity_bits,
                    stopbits=self.stop_bits,
                    bytesize=self.data_bits,
                    timeout=2
            ) as self.serial:
                print(self.baud_rate)
                self.running = True
                while self.running:
                    data = self.__read_data__()
                    if data:
                        self.data_received.emit(data)
        except Exception as e:
            self.serial_error.emit(str(e))

    def __read_data__(self):
        """
        按行接收数据
        :return:
        """
        if self.serial is None or not self.serial.isOpen():
            return

        try:
            # 读取串口数据 例如：b'DDR V1.12 52218f4949 cym 23/07/0'
            byte_array = self.serial.readline()
            if len(byte_array) == 0:
                return None
            # ascii显示
            if self.data_format_recv == 'ascii':
                # 串口接收到的字符串为b'ABC',要转化成unicode字符串才能输出到窗口中去
                data_str = byte_array.decode('utf-8')
            else:
                # 串口接收到的字符串为b'ZZ\x02\x03Z'，要转换成16进制字符串显示
                data_str = ' '.join(format(x, '02x') for x in byte_array)
                if self.auto_line:
                    data_str += '\r\n'
            return data_str
        except Exception as e:
            self.serial_error.emit("接收数据异常！", e)

    def stop(self):
        """
        线程停止
        :return:
        """
        self.running = False
        self.wait()

    def send_data(self, data: str):
        """
        发送数据
        :return:
        """
        if not self.running:
            self.serial_error.emit("请先打开串口！")
            return

        # hex发送 比如：5a 5a 02 03 5a -> b'ZZ\x02\x03Z'
        if self.data_format_send == 'hex':
            data_str = data.strip()
            send_list = []
            while data_str != '':
                try:
                    num = int(data_str[0:2], 16)
                except ValueError:
                    self.serial_error.emit('请输入十六进制数据，以空格分开!')
                    return
                data_str = data_str[2:].strip()
                send_list.append(num)
            if self.auto_line:
                send_list.append('/r/n')
            byte_array = bytes(send_list)
        else:
            if self.auto_line:
                data += '\r\n'
            # ascii发送 比如：'ABC' -> b'ABC'
            byte_array = data.encode('utf-8')

        try:
            self.serial.write(byte_array)
        except Exception as e:
            self.serial_error.emit('发送失败!')

    def isRunning(self):
        return self.running
