#! /usr/bin/env python3
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGridLayout

from components.DisplayTable import DisplayTable
from components.FunctionBar import FunctionBar
from components.LogOutput import LogOutput
from components.MonitorList import MonitorList
from components.NewMonitor import NewMonitor
from components.SettingOptions import SettingOptions
from core.ExceptionHandler import ExceptionHandler
from core.ThreadWorker import RefreshTable, Recording, LoginThread, GetStatusThread
from support.Scrap import getLogTime


class MainWindow(QWidget):
    """
    主窗口类
    """
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)

        title = "Fikker监控工具1.4.3"
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumSize(1280, 768)
        self.setWindowTitle(title)

        self._settings = {}  # 设置选项中的配置信息
        self._tableData = {}  # 所有监控表格信息
        self._loginPools = {}  # 所有登录节点线程
        self._getStatusPools = {}  # 所有获取节点状态线程
        self._mainThreadPools = {}  # 主线程池
        print("%s 终端\n关闭终端会导致程序退出!!\n------------------------" % title)
        self.buildApp()

    def createMonitor(self, info):
        """
        新建监控时初始化， 需要传入监控信息
        将监控名字添加到监控列表选择框并且监控表格切换至新建的表格
        :param info: 监控表格信息
        """
        name = info["name"]
        self._monitorList.addItem(name)
        self._monitorList.setCurrentText(name)
        self.changeTable(info)
        self._mainThreadPools["l"+name] = LoginThread(self, info, parent=self)
        self._mainThreadPools["l"+name].start()

    def changeTable(self, info):
        """
        改变窗口显示的表格为参数info内的表
        首先判断info是否在主类所有监控表格信息里面，如果没有则说明是第一次创建，则创建一个显示表把它添加进去显示
        如果有就不新建直接使用info内的
        :param info: 单个表格信息
        :return:
        """
        if info["name"] not in self._tableData.keys():
            info["displayTable"] = DisplayTable(self)
            self._tableData[info["name"]] = info
            self._displayTable.hide()
            self._displayTable = info["displayTable"]
            self._lay.addWidget(info["displayTable"], 1, 0)
        else:
            self._displayTable.hide()
            self._displayTable = self._tableData[info["name"]]["displayTable"]
            self._displayTable.show()
            return
        # 这里会改变表的行数为表信息中的行数+1, 最后一行用来统计前面的数据
        if len(info["tableData"]) >= 20:
            info["displayTable"].setRowCount(len(info["tableData"]) + 1)
        else:
            info["displayTable"].setRowCount(20)

        for i, line in enumerate(info["tableData"]):
            line[-1] = "登录中"
            info["displayTable"].fillLine(i, line)

    def buildApp(self):
        """
        布置组件和开启后台线程
        """
        self._newMonitor = NewMonitor(self)
        self._settingOptions = SettingOptions(self)

        self._functionBar = FunctionBar(self)
        self._displayTable = DisplayTable(self)
        self._logOutput = LogOutput(self)
        self._monitorList = MonitorList(self)

        self._exceptionHandler = ExceptionHandler(self)

        self._lay = QGridLayout(self)
        self._lay.addWidget(self._functionBar, 0, 0)
        self._functionBar._lay.addWidget(self._monitorList)
        self._lay.addWidget(self._displayTable, 1, 0)
        self._lay.addWidget(self._logOutput, 2, 0)
        self._lay.setContentsMargins(1, 1, 1, 1)
        self._lay.setSpacing(0)
        self.setLayout(self._lay)

        self._refreshTable = RefreshTable(self, parent=self)
        self._refreshTable.updated.connect(self.updateTable)
        self._refreshTable.start()

        self._getStatusThread = GetStatusThread(self, parent=self)
        self._getStatusThread.exception.connect(self.exceptionNotice)
        self._getStatusThread.start()

        self._recording = Recording(self, parent=self)
        self._recording.refreshException.connect(self.refreshExceptionNode)
        self._recording.start()

    def refreshExceptionNode(self, isButton=True):
        curName = self._monitorList.currentText()
        gpools = self._getStatusPools.get(curName, [])
        lpools = self._loginPools.get(curName, [])
        for lt in lpools:
            if lt._nodeLine["needRefresh"]:
                if isButton:
                    lt.wait()
                    lt.start()
                elif lt._nodeLine["loginCount"] >= 3:
                    lt.wait()
                    lt.start()

            for gt in gpools:
                if gt._id == lt._id:
                    gt.wait()
                    gt.start()

    def updateTable(self, row, iter, info):
        """这个槽用来给表格填充数据, 多线程如果不用信号填写会发生意想不到的错误"""
        info["displayTable"].fillLine(row, iter)

    def logPrint(self, message, a=False, color=""):
        """
        打印日志
        :param message: 打印的信息
        :param a: 是否为错误信息
        :param color: 打印字体颜色， 支持 #FFFFFF 格式
        """
        if a:
            color = color if color else "red"
            message = '<font color="%s">%s</font>' % (color, message)
        else:
            message = '<font color="%s">%s</font>' % (color, message)
        self._logOutput.append(message)

    def closeEvent(self, QCloseEvent):
        for i in self._mainThreadPools.values():
            i.terminate()
        for each in self._getStatusPools.values():
            for i in each:
                i.terminate()
        self._recording.terminate()
        self._refreshTable.terminate()
        self._getStatusThread.terminate()

    def exceptionNotice(self, nodeLine, message, sendNotice=True):
        message = getLogTime() + message
        if type(message) == str and bool(message):
            self.logPrint(message, True)
        #
        if sendNotice:
            self._exceptionHandler.notice(nodeLine, message)


def main():
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()








