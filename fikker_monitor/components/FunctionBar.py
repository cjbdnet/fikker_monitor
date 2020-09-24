from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout, QMessageBox


class FunctionBar(QWidget):
    def __init__(self, app):
        super(FunctionBar, self).__init__(app)
        self._app = app

        self.setFixedHeight(30)

        self._input = QLineEdit(self)
        self._search = QPushButton("搜索IP")
        self._new = QPushButton("新建监控")
        self._refresh = QPushButton("刷新异常")
        self._options = QPushButton("设置选项")
        self._tips = QMessageBox()

        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(0)
        self._lay.addWidget(self._input)
        self._lay.addWidget(self._search)
        self._lay.addWidget(self._new)
        self._lay.addWidget(self._refresh)
        self._lay.addWidget(self._options)
        self.setLayout(self._lay)

        self._search.clicked.connect(self.searchSlot)
        self._new.clicked.connect(self.newSlot)
        self._options.clicked.connect(self.optionsSlot)
        self._refresh.clicked.connect(self.refreshSlot)

    def newSlot(self):
        self._app._newMonitor.show()

    def optionsSlot(self):
        self._app._settingOptions.show()

    def refreshSlot(self):
        self._app._recording.refreshException.emit(True)
        self._tips.information(None, "刷新异常", "发送刷新异常信号成功！\n更新状态可能需要一点时间，请暂时不要再次点击此按钮")

    def searchSlot(self):
        value = self._input.text().strip()
        if not value:
            return
        for name, table in self._app._tableData.items():
            for index, line in enumerate(table["tableData"]):
                if value == line[1]:
                    self._app._monitorList.setCurrentText(name)
                    self._app._displayTable.selectRow(index+1)  # 这里如果只选择需要的行，并且行已经是选择状态, 页面就算没显示出行也不会跳转过去,
                    self._app._displayTable.selectRow(index)    # 也没找到清除已选择选择的api，就使用这样的笨方法
