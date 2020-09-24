from datetime import datetime
from json import loads
from time import sleep
from requests import get
from PyQt5.QtCore import QThread, pyqtSignal
from support.Scrap import getFloat, calStatistics, saveCurrentFlow, get_size, flowIsLowLevel


class Login(QThread):
    """
    这个线程会根据传入的参数登录fikker节点，获取fikker的sessionID值
    """
    exception = pyqtSignal(dict, str, bool)

    def __init__(self, info, i):
        """
        :param app: 主窗口类：main.py -> class MainWindow
        :param node: 登录信息: {"SessionID": None, "login":(ip, port, password)}
        :param i: 当前需要登录的节点信息所在位置
        :param info: 整个监控的所有信息
        """
        super(self.__class__, self).__init__()
        self._info = info
        self._i = i
        self._nodeLine = info["node"][i]
        self._url = "http://%s:%s/fikker/webcache.fik?type=sign&cmd=in&RequestID=test-login&Username=admin&Password=%s" % \
                    self._nodeLine["flogin"]
        self._id = hash(str(self._nodeLine["flogin"]))
        self._dataLine = info["tableData"][i]

    def run(self):
        """
        请求生成的fikker节点登录url， 如果请求失败则会在监控表中状态列改为异常
        读取登录fikker节点返回的信息， 保存SessionID并在监控表中状态列改为正常
        """
        head = "[登录][%s][%s]" % (self._dataLine[0], self._dataLine[1])
        try:
            res = get(self._url, timeout=90)
        except Exception:
            self._nodeLine["needRefresh"] = True
            self._nodeLine["loginCount"] += 1
            self._dataLine[-1] = "异常"
            message = head + "尝试连接Fikker失败, 第%s次" % self._nodeLine["loginCount"]
            self.exception.emit(self._nodeLine, message, True)
        else:
            ret = loads(res.text)
            if ret["Return"] == "True":
                self._nodeLine["loginCount"] = 0
                self._nodeLine["needRefresh"] = False
                self._nodeLine["SessionID"] = ret["SessionID"]
                self._dataLine[-1] = "正常"
            else:
                self._nodeLine["loginCount"] += 1
                self._nodeLine["needRefresh"] = True
                self._dataLine[-1] = "异常"
                if ret["ErrorNo"] == "20":
                    self._nodeLine["SessionID"] = False
                    message = head + "已连接到Fikker，但是用户名或密码错误导致登陆失败"
                else:
                    message = head + "已连接到Fikker, 但是返回异常信息，错误号: %s" % ret["ErrorNo"]
                self.exception.emit(self._nodeLine, message, True)


class LoginThread(QThread):
    """
    这个是开启登录所有节点的主线程
    """

    def __init__(self, app, info, parent=None):
        """
        :param app: 主窗口类：main.py -> class MainWindow
        :param info: 整个监控的所有信息
        :param parent: 父线程
        """
        super(self.__class__, self).__init__(parent)
        self._app = app
        self._info = info

    def run(self):
        """
        从监控信息中读取节点登录信息多线程去登录, 登录线程全部登陆完后退出线程
        启动线程时会判断该节点是否登录过，如果登录了则跳过登录
        """
        curName = self._info["name"]
        pool = self._app._loginPools.get(curName, [])

        if not pool:
            for i, line in enumerate(self._info["node"]):
                t = Login(self._info, i)
                t.exception.connect(self._app.exceptionNotice)
                t.start()
                pool.append(t)
            else:
                self._app._loginPools[curName] = pool
        else:
            for t in pool:
                td = t._dataLine
                tl = t._nodeLine
                if tl["SessionID"] is not None:
                    continue
                if tl["loginCount"] >= 2:
                    message = "[登录][%s][%s]尝试连接失败三次，服务器或Fikker可能存在问题, 已停止自动重新连接!\n仍可手动点击【刷新异常】按钮重试" % (td[0], td[1])
                    t.exception.emit(tl, message, True)
                    tl["SessionID"] = False
                    tl["loginCount"] += 1  # 实际运行到这里时已经是第三次
                    continue
                t.wait()
                t.start()


class GetStatus(QThread):
    """
    这个线程会去请求fikker实时监控接口，将获取的信息更新在监控信息表中
    """
    exception = pyqtSignal(dict, str, bool)

    def __init__(self, nodeLine, i, info):
        """
        :param app: 主窗口类
        :param i: 节点在信息表中所在位置
        :param info: 监控信息
        """
        super(self.__class__, self).__init__()
        self._id = hash(str(nodeLine["flogin"]))
        self._nodeLine = nodeLine
        self._i = i
        self._info = info
        self._dataLine = info["tableData"][i]
        self._lastStatus = None

    def run(self):
        """
        实时获取节点信息更新在监控表中
        """
        # size = get_size(self._app._tableData)
        # print(size)
        url = "http://%s:%s/fikker/webcache.fik?type=realtime&cmd=list&SessionID=%s" % \
                    (self._nodeLine["flogin"][0], self._nodeLine["flogin"][1], self._nodeLine["SessionID"])
        message = "[刷新][%s][%s]" % (self._dataLine[0], self._dataLine[1])
        try:
            res = loads(get(url, timeout=60).text)
        except Exception as e:
            self._dataLine[-1] = "异常"
            message += "连接获取实时节点信息API失败，稍后会尝试重新连接"
            self.exception.emit(self._nodeLine, message, False)
            self._nodeLine["getStatusErrorNum"] += 1
            if self._nodeLine["getStatusErrorNum"] >= 5:
                self._nodeLine["needRefresh"] = True
        else:
            if res["Return"] == "False":
                if int(res["ErrorNo"].strip()) == 21:
                    # 错误号21是会话超时
                    self._nodeLine["needRefresh"] = True

                self._dataLine[-1] = "异常"
                self._nodeLine["getStatusErrorNum"] += 1
                self._nodeLine["SessionID"] = None
                message += "获取实时节点信息失败，错误号: %s" % res["ErrorNo"]
                self.exception.emit(self._nodeLine, message, False)
                return

            if self._lastStatus is not None:
                ti = int(res["CurrentTickCount"]) - int(self._lastStatus["CurrentTickCount"])  # time interval
                rbw = int(res["TotalRecvFromResponseKB"]) - int(self._lastStatus["TotalRecvFromResponseKB"])
                ubw = int(res["TotalSendKB"]) - int(self._lastStatus["TotalSendKB"])

                self._dataLine[2] = "%.3f" % (ubw / ti * 8)
                self._dataLine[3] = "%.3f" % (rbw / ti * 8)

            self._dataLine[4] = res["CurrentUserConnections"]
            self._dataLine[5] = res["CurrentUpstreamConnections"]
            self._dataLine[6] = "%.3f MB" % (int(res["SizeOfDiskCachesIndex"]) / 1024)
            self._dataLine[7] = "%.3f " % (int(res["FikUsedMemSizeKB"]) / int(res["TotalPhyMemSizeKB"]) * 100)
            self._dataLine[8] = "%.3f GB" % (float(res["CacheUsedMemSize"]) / 1024 / 1024)
            self._dataLine[9] = res["NumOfCaches"]
            self._dataLine[-1] = "正常"
            self._nodeLine["getStatusErrorNum"] = 0
            self._nodeLine["needRefresh"] = False

            self._lastStatus = res


class GetStatusThread(QThread):
    """
    这个线程会读取监控信息表中所有节点多线程去获取实时信息, 如果手动传入了监控信息则会改为记录状态
    记录状态： 非记录状态此线程是获取主窗口当前选择的监控表信息实时获取数据，记录状态是流量统计时
    后台刷新其他监控表信息获取数据，并且只获取三次后就退出线程
    """
    exception = pyqtSignal(dict, str, bool)

    def __init__(self, app, curName=None, parent=None):
        """
        :param app: 主窗口类
        :param info: 监控信息表
        :param parent: 父线程
        """
        super(self.__class__, self).__init__(parent)
        self._app = app
        self._curName = curName
        self._isRecord = False if curName is None else True

    def run(self):
        """
        开启线程后进入死循环，首先根据是否传入监控信息表判断是否为记录状态，如果不是就获取当前选中的监控信息表
        接下来读取表中节点信息， 判断是否登录， 如果登录了会生成url多线程去获取实时数据。
        如果是记录状态，则会在第三次保存当前流量数据后退出线程
        """
        temp = []
        cycles = 3 if self._isRecord else True
        while cycles:
            tn = self._app._settings["ThreadsNum"]
            if not self._isRecord:
                self._curName = self._app._monitorList.currentText()

            try:
                self._info = self._app._tableData[self._curName]
            except KeyError:
                sleep(1)
                continue
            node = self._info["node"]

            pool = self._app._getStatusPools.get(self._curName, [])

            if len(node) != len(pool):
                for i, line in enumerate(node):
                    if len(temp) >= tn:
                        for tgs in temp:
                            if tgs.isRunning():
                                tgs.wait()
                        else:
                            temp.clear()
                    if not bool(line["SessionID"]):
                        continue
                    if not line["gotStatus"]:
                        gs = GetStatus(line, i, self._info)
                        gs.exception.connect(self._app.exceptionNotice)
                        pool.append(gs)
                        temp.append(gs)
                        line["gotStatus"] = True
                temp.clear()
                self._app._getStatusPools[self._curName] = pool

            for t in pool:
                if len(temp) >= tn:
                    for tgs in temp:
                        if tgs.isRunning():
                            tgs.wait()
                    else:
                        temp.clear()
                if t.isRunning():
                    t.wait()
                t.start()
                temp.append(t)
            else:
                temp.clear()

            if self._isRecord:
                result = calStatistics(self._info, isRound=True)
                if cycles == 1:
                    path = self._app._settings["TrafficRecordPath"]
                    name = self._info["name"]
                    self.lowFlowNotice(result[0], name)
                    saveCurrentFlow(result, path, name)
                cycles -= 1

            sleep(self._app._settings["NodeUpdateRate"])

    def lowFlowNotice(self, curFlow, name):
        settings = self._app._settings
        if not settings["IsLowFlowNotice"]:
            return
        now = datetime.now()
        nname = name.split("-")[0]
        try:
            threshold = settings["threshold"][nname]
        except KeyError:
            return
        try:
            level = threshold[str(now.hour)]
        except KeyError:
            message = "[%s]阈值配置中未找到对应当前时间点: %s" % (nname, now.hour)
            self._app._getStatusThread.exception.emit({}, message, False)
            return
        if curFlow < int(level):
            message = "[%s]当前流量：%s, 最低流量阈值：%s\n" % (nname, curFlow, level)
            self._app._getStatusThread.exception.emit({}, message, True)


class RefreshTable(QThread):
    """
    这个线程会实时刷新当前选中的监控信息表。定义了一个updated信号，这个信号用来刷新窗口显示
    """
    updated = pyqtSignal(int, list, dict)

    def __init__(self, app, parent=None):
        super(self.__class__, self).__init__(parent)
        self._app = app

    def run(self):
        """
        线程进入死循环状态，每次循环获取当前监控信息内容写入窗口表格中， 写入完毕刷新一次
        """
        while True:
            try:
                name = self._app._monitorList.currentText()
                curInfo = self._app._tableData[name]
                data = curInfo["tableData"]
            except KeyError:
                sleep(0.5)
            else:
                total = ["四舍五入", "统计", 0, 0, 0, 0]
                for i, line in enumerate(data):
                    self.updated.emit(i, line, curInfo)
                    total[2] = (getFloat(total[2]) + getFloat(line[2]))
                    total[3] = (getFloat(total[3]) + getFloat(line[3]))
                    total[4] = (getFloat(total[4]) + getFloat(line[4]))
                    total[5] = (getFloat(total[5]) + getFloat(line[5]))
                else:
                    total[2] = str(round(total[2]))
                    total[3] = str(round(total[3]))
                    total[4] = str(round(total[4]))
                    total[5] = str(round(total[5]))
                    self.updated.emit(len(data), total, curInfo)
                    curInfo["displayTable"].viewport().update()
            finally:
                sleep(self._app._settings["UIRefreshRate"])


class Recording(QThread):
    """
    这个线程会记录每隔一段时间记录流量统计
    """
    refreshException = pyqtSignal(bool)

    def __init__(self, app, parent=None):
        super(self.__class__, self).__init__(parent)
        self._app = app

    def run(self):
        while True:
            ml = self._app._monitorList
            for i in range(ml.count()):
                name = ml.itemText(i)
                info = self._app._tableData.get(name)

                lt = self._app._mainThreadPools.get("l"+name)
                gst = self._app._mainThreadPools.get("g"+name)
                if lt is None:
                    lt = LoginThread(self._app, info)
                    self._app._mainThreadPools["l"+name] = lt
                if gst is None:
                    gst = GetStatusThread(self._app, name)
                    self._app._mainThreadPools["g"+name] = gst

                lt.start()
                lt.wait()

                gst.start()
                gst.wait()
            else:
                # self._app._recording.refreshException.emit(False)
                self.refreshException.emit(False)
                # sleep(10)
                sleep(self._app._settings["RecordingInterval"])
