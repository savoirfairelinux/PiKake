# -*- coding: utf-8 -*-

import sys
import time

from PyQt5.QtCore import QUrl, QTimer, Qt
from PyQt5.QtWidgets import QStackedLayout, QWidget
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings
from PyQt5.Qt import QApplication

from multiprocessing import Process, Queue
from threading import Thread

from pikake.task import Task

class Browser(QWebView):

    def __init__(self, url, display_time, refresh = False):
        super(QWebView, self).__init__()
        self.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
        new_url = QUrl(url)
        self.load(new_url)
        self.showFullScreen()
        self.refresh = refresh
        self.display_time = display_time
        self.page().mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.page().mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)

class BrowserProcess(Process):

    def __init__(self, url, display_time, refresh = False):
        super(Process, self).__init__()
        self.url = url
        self.display_time = display_time
        self.refresh = refresh
        self.browser = None
        self.queue = Queue()

    def command_thread(self, browser):
        while True:
            time.sleep(0.1)
            if not self.queue.empty():
                command = self.queue.get()

                if command == 'show':
                    browser.setFocus()
                    browser.activateWindow()

    def run(self):
        self.browser_app = QApplication(sys.argv)
        self.browser = Browser(self.url, self.display_time, self.refresh)
        self.browser.show()

        t = Thread(target = self.command_thread, args = (self.browser,))
        t.start()

        self.browser_app.exec_()
