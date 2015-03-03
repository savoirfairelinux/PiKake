# -*- coding: utf-8 -*-

import sys

from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWidgets import QStackedLayout, QWidget
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings
from PyQt5.Qt import QApplication

from multiprocessing import Process

from pikake.task import Task

class Browser(QWebView):

    def __init__(self, url):
        super(QWebView, self).__init__()
        self.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
        new_url = QUrl(url)
        self.load(new_url)
        self.showFullScreen()

        self.changeTabSignal = QTimer()
        self.changeTabSignal.setInterval(15000)
        self.changeTabSignal.timeout.connect(self.next_tab)

    def start(self):
        self.changeTabSignal.start()

    def next_tab(self):
        next_index = (self.layout.currentIndex() + 1) % self.layout.count()
        self.layout.setCurrentIndex(next_index)


class BrowserProcess(Process):

    def __init__(self, url):
        super(Process, self).__init__()
        self.url = url

    def run(self):
        print("RUN")
        self.browser_app = QApplication(sys.argv)
        self.browser = Browser(self.url)
        self.browser.show()
        self.browser_app.exec_()
