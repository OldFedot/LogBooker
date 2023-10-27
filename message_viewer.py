from PyQt6.QtWidgets import QTextBrowser
from PyQt6 import QtCore, QtGui


class LogMessageViewer(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setGeometry(QtCore.QRect(430, 27, 470, 491))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.setFont(font)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setObjectName("text_browser")
        version = "Logbooker v2.21.dev Developed by Timofey Fedotenko\n"
        start_message = """For bag reports, problems, ideas: TimofeyFedotenko@gmail.com\n\n"""
        self.append(version + start_message)

    def append_log_message(self, message, err=False, service=False):
        if err:
            msg_tmp = "Error: " + message
            self.append(f"<p style='color: red'>{msg_tmp}</p>")
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        elif service:
            self.append(f"<p style='color: blue'>{message}</p>")
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        else:
            self.append("..." + message)
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
