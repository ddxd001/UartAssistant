from PyQt5.QtWidgets import QComboBox, QMessageBox, QMainWindow, QButtonGroup, QPushButton, QLineEdit, QFileDialog, \
    QApplication, QWidget

from Settings import Ui_MainWindow


class SettingsThread(QWidget, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def open_settings(self):
        self.show()
