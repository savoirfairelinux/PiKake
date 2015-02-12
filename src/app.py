#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json

from PyQt4.QtCore import QUrl, QTimer
from PyQt4.QtGui import QApplication, QStackedLayout, QWidget
from PyQt4.QtWebKit import QWebView, QWebSettings

class BrowserTab(QWebView):

    def __init__(self, url):
        QWebView.__init__(self)
        self.load(QUrl(url))
        

class Browser(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.layout = QStackedLayout()
        self.layout.setStackingMode(1)
        self.showFullScreen()

        self.changeTabSignal = QTimer()
        self.changeTabSignal.setInterval(5000)
        self.changeTabSignal.timeout.connect(self.next_tab)
        self.setLayout(self.layout)

    def set_urls(self, urls):
        i = 0
        for url in urls:
            tab = BrowserTab(url)
            tab.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
            self.layout.insertWidget(i, tab)

    def next_tab(self):
        next_index = (self.layout.currentIndex() + 1) % self.layout.count()
        self.layout.setCurrentIndex(next_index)

    def start(self):
        self.changeTabSignal.start()


if __name__ == '__main__':

    data = json.load(open('./config.json', 'r'))

    app = QApplication(sys.argv)
     
    browser = Browser()
    browser.set_urls(data['tabs'])
    browser.start()
    browser.show()

    app.exec_()
