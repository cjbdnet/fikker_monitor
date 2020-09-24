from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView

from support.Scrap import genNameFromPath, parseLoginFile


class DisplayTable(QTableWidget):
    updated = pyqtSignal(int, list)

    def __init__(self, app):
        super(DisplayTable, self).__init__()
        self._app = app
        self.setAcceptDrops(True)
        self.setColumnCount(11)
        self.setRowCount(20)
        self.setHorizontalHeaderLabels(
            ["备注", "IP", "用户宽带(Mbps)", "源站带宽(Mbps)", "用户连接数", "源站连接数", "硬盘索引尺寸",
             "Fik内存占比(%)", "缓存尺寸", "缓存数量", "当前状态"])
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.updated.connect(self.fillLine)

    def fillLine(self, row, iterator):
        """
        一次填写一行数据
        :param row: 填写的行数
        :param iterator: 填写的一行内容
        :return:
        """
        for i, v in enumerate(iterator):
            self.fillIn(row, i, v)

    def fillIn(self, x, y, v):
        """
        填写一个单元格
        :param x: 行格数
        :param y: 列格数
        :param v: 值
        """
        if v is None:
            return
        item = self.item(x, y)
        if item is None:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(x, y, item)
        if v == "正常":
            item.setForeground(QBrush(QColor(0, 200, 0)))
        elif v == "异常":
            item.setForeground(QBrush(QColor(200, 0, 0)))
        elif v == "登录中":
            item.setForeground(QBrush(QColor(0, 0, 200)))

        item.setText(v)

    def dragEnterEvent(self, event):
        """
        文件拖入时判断是否为指定类型
        """
        fileType = event.mimeData().text().split('.')[-1].lower()
        if fileType == "xlsx" or fileType == "xls" or fileType == "txt":
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """
        文件拖入移动时再次判断
        """
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        文件拖入松开时读取文件数据并生成初始信息，然后创建一个新的监控表格页面
        """
        info = {"isLogin": False}
        path = event.mimeData().text().replace("file:///", "")
        info["path"] = path
        info["name"] = genNameFromPath(path, self._app)
        allInfo = parseLoginFile(info)
        self._app.createMonitor(allInfo)
        self._app.logPrint("新建监控成功:-> %s" % info["path"])
