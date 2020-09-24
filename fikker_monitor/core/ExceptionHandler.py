from PyQt5.QtCore import QThread
from telegram import Bot


class ExceptionHandlerThread(QThread):
    def __init__(self, settings, bot, message):
        super(self.__class__, self).__init__()
        self.setArgs(settings, bot, message)

    def setArgs(self, settings, bot, message):
        self._settings = settings
        self._bot = bot
        self._message = message
        self._chatId = self._settings["ChatID"]

    def run(self):
        if self._settings["IsBot"]:
            try:
                self._bot.send_message(text=self._message, chat_id=self._chatId)
            except:
                print("机器人发送信息失败")

        elif self._settings["IsEmail"]:
            pass


class ExceptionHandler:
    def __init__(self, app):
        self._app = app
        self._settings = app._settings
        self._bot = Bot(token=self._settings["BotToken"])
        self._workerPools = []

    def notice(self, target, message):
        # message = "%s:%s出现问题, 此为测试信息" % (target["flogin"][0], target["flogin"][1])

        for w in self._workerPools:
            if w.isFinished():
                w.wait()
                w.setArgs(self._settings, self._bot, message)
                w.start()
                break
        else:
            eth = ExceptionHandlerThread(self._settings, self._bot, message)
            eth.start()
            self._workerPools.append(eth)

