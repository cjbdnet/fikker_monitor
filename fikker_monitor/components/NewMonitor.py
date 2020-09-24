from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLineEdit, QGridLayout, QLabel, QFileDialog, QPushButton

from support.Scrap import genNameFromPath, parseLoginFile


class NewMonitor(QDialog):
    def __init__(self, app):
        super(NewMonitor, self).__init__(app, flags=Qt.WindowCloseButtonHint)
        self._app = app
        self.resize(300, 150)
        self.setWindowTitle("新建监控")

        self._loginTables = []

        self._fileDialog = QFileDialog()

        self._fileInput = QLineEdit(self)
        self._fileInput.setReadOnly(True)
        self._select = QPushButton("浏览")
        self._name = QLineEdit(self)
        self._login = QPushButton("导入并登录")

        self._select.clicked.connect(self.selectSlot)
        self._login.clicked.connect(self.submitSlot)

        self._lay = QGridLayout(self)
        self._lay.setContentsMargins(3, 3, 3, 3)
        self._lay.setSpacing(0)
        self._lay.addWidget(QLabel("监控备注:"), 0, 0, 1, 1)
        self._lay.addWidget(self._name, 0, 1, 1, 5)
        self._lay.addWidget(QLabel("登录文件:"), 1, 0, 1, 1)
        self._lay.addWidget(self._fileInput, 1, 1, 1, 4)
        self._lay.addWidget(self._select, 1, 5, 1, 1)
        self._lay.addWidget(self._login, 2, 1, 1, 4)

    def selectSlot(self):
        self.p, self.t = self._fileDialog.getOpenFileName(self, "选取文件", filter="可用类型(*.txt *.xlsx *.xls)")
        self._fileInput.setText(self.p)

    def submitSlot(self):
        name = self._name.text().strip()
        fileInput = self._fileInput.text()
        if name in self._app._tableData.keys():
            self._name.clear()
            self._name.setPlaceholderText("已有相同监控名称，请重新输入")
            self._app.logPrint("新建监控失败:-> 已有相同监控备注", 1)
            return
        if not fileInput:
            self._fileInput.clear()
            self._fileInput.setPlaceholderText("请选择文件")
            self._app.logPrint("新建监控失败:-> 请选择登录文件", 1)
            return
        if not name:
            name = genNameFromPath(fileInput, self._app)

        info = {"name": name, "path": fileInput}

        allInfo = parseLoginFile(info)
        self._app.createMonitor(allInfo)
        self._app.logPrint("新建监控成功:-> %s" % info["path"])
        self.close()

    def closeEvent(self, QCloseEvent):
        self._name.setPlaceholderText("")
        self._fileInput.setPlaceholderText("")
        self._name.clear()
        self._fileInput.clear()
