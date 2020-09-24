from PyQt5.QtWidgets import QComboBox


class MonitorList(QComboBox):
    def __init__(self, app):
        super(MonitorList, self).__init__(app)
        self._app = app

        self.setFixedWidth(200)
        self.currentTextChanged.connect(self.updateTable)

    def updateTable(self):
        name = self.currentText()
        try:
            allInfo = self._app._tableData[name]
        except KeyError:
            return
        self._app.changeTable(allInfo)
