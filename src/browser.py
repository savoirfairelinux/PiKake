# -*- coding: utf-8 -*-

from PyQt4.QtCore import QUrl, QTimer
from PyQt4.QtGui import QStackedLayout, QWidget
from PyQt4.QtWebKit import QWebView, QWebSettings

class Browser(QWebView):

    def __init__(self, url):
        super(QWebView, self).__init__()
        self.load(QUrl(url))
        self.showFullScreen()
        self.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)

        self.changeTabSignal = QTimer()
        self.changeTabSignal.setInterval(5000)
        self.changeTabSignal.timeout.connect(self.next_tab)

    def start(self):
        self.changeTabSignal.start()

    def next_tab(self):
        next_index = (self.layout.currentIndex() + 1) % self.layout.count()
        self.layout.setCurrentIndex(next_index)
