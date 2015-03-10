# -*- coding: utf-8 -*-

import sys
import time

from PyQt5.QtCore import QUrl, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QStackedLayout, QWidget
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings
from PyQt5.Qt import QApplication

from multiprocessing import Process, Queue
from threading import Thread

from pikake.task import Task


class Browser(QWebView):

    refresh_signal = pyqtSignal()

    def __init__(self, url, display_time, refresh=False):
        super(QWebView, self).__init__()

        self.url = url
        self.refresh = refresh
        self.display_time = display_time

        self.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
        self.load(QUrl(url))
        self.showFullScreen()

        self.refresh_signal.connect(self.reload)

        self.page().mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.page().mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)

    def get_attrs(self):
        values = {}
        values['url'] = self.url
        values['display_time'] = self.display_time
        values['refresh'] = self.refresh

        return values


class BrowserProcess(Process):

    def __init__(self, url, display_time, refresh=False):
        super(Process, self).__init__()
        self.url = url
        self.display_time = display_time
        self.refresh = refresh
        self.browser = None
        self.queue = Queue()
        self.response_queue = Queue()

    def command_thread(self, browser):
        print(browser.refresh_signal)
        while True:
            time.sleep(0.1)
            if not self.queue.empty():
                command = self.queue.get()

                if command == 'show':
                    browser.setFocus()
                    browser.activateWindow()
                elif command == 'get_attrs':
                    attrs = browser.get_attrs()
                    self.response_queue.put(attrs)
                elif command == 'reload':
                    if browser.refresh:
                        browser.refresh_signal.emit()

    def run(self):
        self.browser_app = QApplication(sys.argv)
        self.browser = Browser(self.url, self.display_time, self.refresh)
        self.browser.show()

        t = Thread(target=self.command_thread, args=(self.browser,))
        t.start()

        self.browser_app.exec_()
