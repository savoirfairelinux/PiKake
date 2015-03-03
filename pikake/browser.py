# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWidgets import QStackedLayout, QWidget
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings

class Browser(QWebView):

    def __init__(self, url):
        super(QWebView, self).__init__()
        self.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
#         self.settings().setLocalStoragePath('/home/fred/tmp/')
        new_url = QUrl(url)
#         new_url.setPassword('kaji')
#         new_url.setUserName('kaji')
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
