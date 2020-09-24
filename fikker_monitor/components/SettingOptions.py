from json import load
from os import getcwd
from os.path import join

from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QRadioButton, QVBoxLayout, \
    QGridLayout, QFrame, QComboBox, QCheckBox, QFileDialog, QGroupBox
from PyQt5.QtCore import Qt

from support.Scrap import configParserToDict


class SettingOptions(QDialog):

    def __init__(self, app):
        super(self.__class__, self).__init__(app, flags=Qt.WindowCloseButtonHint)
        self._app = app
        self._settings = {"threshold":{}}

        self.setWindowTitle("设置选项")
        self.setFixedSize(600, 400)

        self._fileDialog = QFileDialog()

        self._lay = QVBoxLayout(self)

        # ----------------------------------------------------------
        self._ri = QLineEdit(self)  # 记录间隔时间 Recording interval
        self._ri.setValidator(QIntValidator(1, 65535))
        self._trp = QLineEdit(self)  # 流量记录路径 Traffic record path
        self._trpSelect = QPushButton("浏览")
        self._trpSelect.setFixedWidth(50)

        self._nur = QLineEdit(self)  # 节点信息更新频率 Refresh rate
        self._uirr = QLineEdit(self)  # ui刷新频率
        self._tn = QLineEdit(self)  # 线程数 thread num
        self._nur.setValidator(QIntValidator(1, 65535))
        self._uirr.setValidator(QIntValidator(1, 65535))
        self._tn.setValidator(QIntValidator(1, 128))

        self._frame1 = QGroupBox("通用选项")
        self._frame1Lay = QGridLayout()

        self._frame1Lay.addWidget(QLabel("记录间隔时间:"), 0, 0, 1, 1)
        self._frame1Lay.addWidget(self._ri, 0, 1, 1, 1)
        self._frame1Lay.addWidget(QLabel("流量记录路径:"), 0, 2, 1, 1)
        self._frame1Lay.addWidget(self._trp, 0, 3, 1, 3)
        self._frame1Lay.addWidget(self._trpSelect, 0, 6, 1, 1)
        self._frame1Lay.addWidget(QLabel("节点信息更新频率:"), 1, 0, 1, 1)
        self._frame1Lay.addWidget(self._nur, 1, 1, 1, 1)
        self._frame1Lay.addWidget(QLabel("UI刷新频率:"), 1, 2, 1, 1)
        self._frame1Lay.addWidget(self._uirr, 1, 3, 1, 1)
        self._frame1Lay.addWidget(QLabel("线程数:"), 1, 4, 1, 1)
        self._frame1Lay.addWidget(self._tn, 1, 5, 1, 1)

        self._frame1.setLayout(self._frame1Lay)
        # ----------------------------------------------------------

        # ----------------------------------------------------------
        self._bt = QLineEdit(self)  # 机器人token Bot token
        self._ea = QLineEdit(self)  # 邮箱地址 Email address
        self._cid = QLineEdit(self)  # 机器人通知群组  Chat ID
        self._btSelect = QRadioButton("机器人")
        self._btSelect.setChecked(True)
        self._eaSelect = QRadioButton("邮箱")

        self._frame2 = QGroupBox("通知配置")
        self._frame2Lay = QGridLayout()

        self._frame2Lay.addWidget(QLabel("机器人Token:"), 0, 0, 1, 1)
        self._frame2Lay.addWidget(self._bt, 0, 1, 1, 2)
        self._frame2Lay.addWidget(QLabel("对话ID:"), 0, 3, 1, 1)
        self._frame2Lay.addWidget(self._cid, 0, 4, 1, 2)
        self._frame2Lay.addWidget(QLabel("邮箱地址:"), 1, 0, 1, 1)
        self._frame2Lay.addWidget(self._ea, 1, 1, 1, 2)
        self._frame2Lay.addWidget(QLabel("通知方式:"), 1, 3, 1, 1)
        self._frame2Lay.addWidget(self._btSelect, 1, 4, 1, 1)
        self._frame2Lay.addWidget(self._eaSelect, 1, 5, 1, 1)

        self._frame2.setLayout(self._frame2Lay)
        # ----------------------------------------------------------

        self._frame3 = QGroupBox("最低阈值配置")
        self._frame3Lay = QGridLayout()

        self._timeSelect = QComboBox(self)  # 选择时间点
        self._timeSelect.currentTextChanged.connect(self.tsChangedSlot)
        self._sf = QLineEdit(self)  # 标准流量 std flow
        self._sf.setValidator(QIntValidator(1, 999999))
        self._sf.textChanged.connect(self.sfChangedSlot)
        self._lfn = QCheckBox(self)  # low flow notice
        self._ml = QComboBox(self)  # monitor list
        self._ml.currentTextChanged.connect(self.mlChangedSlot)
        self._it = QPushButton("导入流量阈值")
        self._it.clicked.connect(self.importSlot)

        self._frame3Lay.addWidget(QLabel("监控列表:"), 0, 0)
        self._frame3Lay.addWidget(self._ml, 0, 1)
        self._frame3Lay.addWidget(QLabel("选择时间:"), 0, 2)
        self._frame3Lay.addWidget(self._timeSelect, 0, 3, 1, 2)

        self._frame3Lay.addWidget(QLabel("流量阈值:"), 1, 0)
        self._frame3Lay.addWidget(self._sf, 1, 1)
        self._frame3Lay.addWidget(QLabel("低流量通知:"), 1, 2)
        self._frame3Lay.addWidget(self._lfn, 1, 3)
        self._frame3Lay.addWidget(self._it, 1, 4)

        self._frame3.setLayout(self._frame3Lay)
        # ----------------------------------------------------------

        self._lay.addWidget(self._frame1)
        self._lay.addWidget(self._frame2)
        self._lay.addWidget(self._frame3)
        self.setLayout(self._lay)

        self.initSettings()

    def initSettings(self):
        cwd = join(getcwd(), "log")
        # 必须填写
        token = ""    # 飞机机器人token str
        cid = 0       # 机器人消息频道 int
        
        self._ri.setText(str(180))
        self._trp.setText(cwd)
        self._bt.setText(token)
        self._cid.setText(str(cid))
        self._nur.setText(str(15))
        self._uirr.setText(str(3))
        self._tn.setText(str(8))

        self._settings["RecordingInterval"] = 180
        self._settings["TrafficRecordPath"] = cwd
        self._settings["BotToken"] = token
        self._settings["ChatID"] = cid
        self._settings["IsBot"] = True
        self._settings["IsEmail"] = False
        self._settings["EmailAddress"] = ''
        self._settings["NodeUpdateRate"] = 15
        self._settings["UIRefreshRate"] = 3
        self._settings["ThreadsNum"] = 8
        self._settings["IsLowFlowNotice"] = False

        self._app._settings = self._settings

    def saveChanged(self):
        if not self._ri.text():
            self._ri.setText(str(self._settings["RecordingInterval"]))
        if not self._trp.text():
            self._trp.setText(self._settings["TrafficRecordPath"])
        if not self._bt.text():
            self._bt.setText(self._settings["BotToken"])
        if not self._cid.text():
            self._cid.setText(str(self._settings["ChatID"]))
        if not self._nur.text():
            self._nur.setText(str(self._settings["NodeUpdateRate"]))
        if not self._uirr.text():
            self._uirr.setText(str(self._settings["UIRefreshRate"]))
        if not self._tn.text():
            self._tn.setText(str(self._settings["ThreadsNum"]))

        self._settings["RecordingInterval"] = int(self._ri.text())
        self._settings["ChatID"] = int(self._cid.text())
        self._settings["EmailAddress"] = self._ea.text()
        self._settings["BotToken"] = self._bt.text()
        self._settings["TrafficRecordPath"] = self._trp.text()
        self._settings["IsBot"] = True if self._btSelect.isChecked() else False
        self._settings["IsEmail"] = True if self._eaSelect.isChecked() else False
        self._settings["NodeUpdateRate"] = int(self._nur.text())
        self._settings["UIRefreshRate"] = int(self._uirr.text())
        self._settings["ThreadsNum"] = int(self._tn.text())
        self._settings["IsLowFlowNotice"] = True if self._lfn.isChecked() else False

        self._app._settings = self._settings


    def hideEvent(self, *args, **kwargs):
        self.saveChanged()

    def closeEvent(self, QCloseEvent):
        self.saveChanged()

    def importSlot(self):
        p, t = self._fileDialog.getOpenFileName(self, "选取文件", filter="可用类型(*.ini *.json)")
        if not p:
            return
        ft = p.split(".")[-1].lower()
        if ft == "ini":
            self._threshold = configParserToDict(p)
        else:
            self._threshold = load(open(p, encoding="utf-8"))

        keys = self._settings["threshold"].keys()
        for key in self._threshold:
            if key in keys:
                continue
            self._ml.addItem(key)
        self._settings["threshold"].update(self._threshold)
        self.tsChangedSlot()
        self._lfn.setChecked(True)

    def mlChangedSlot(self):
        self._timeSelect.clear()
        name = self._ml.currentText()
        for time, value in self._threshold[name].items():
            self._timeSelect.addItem(time)
        self.tsChangedSlot()

    def tsChangedSlot(self):
        name = self._ml.currentText()
        time = self._timeSelect.currentText()
        try:
            self._sf.setText(str(self._threshold[name][time]))
        except KeyError:
            pass
        self.sfChangedSlot()

    def sfChangedSlot(self):
        name = self._ml.currentText()
        time = self._timeSelect.currentText()
        if not self._sf.text():
            self._sf.setText(str(self._threshold[name][time]))
        else:
            self._threshold[name][time] = self._sf.text()

