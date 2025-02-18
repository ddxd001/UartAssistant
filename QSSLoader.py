class QSSLoader:
    def __init__(self):
        pass

    @staticmethod
    def read_qss_file(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()