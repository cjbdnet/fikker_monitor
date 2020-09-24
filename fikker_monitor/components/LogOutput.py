from PyQt5.QtWidgets import QTextEdit


class LogOutput(QTextEdit):
    def __init__(self, app):
        super(LogOutput, self).__init__()
        self._app = app

        self.setFixedHeight(100)

        self.setReadOnly(True)
        self.setHtml('''
            <div style="color:green">
            此处为日志输出框，可在"设置选项"中配置相关设置<br/>
            - - - - - - - - - - - - - - - - - - - - - - - -
            </div>''')
        cursor = self.textCursor()
        cursor.movePosition(cursor.End)
        self.setTextCursor(cursor)

