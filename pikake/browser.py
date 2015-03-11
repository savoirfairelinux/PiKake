# -*- coding: utf-8 -*-

import sys
import time

from PyQt5.QtCore import QUrl, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QStackedLayout, QWidget
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings
from PyQt5.Qt import QApplication
import PyQt5

from multiprocessing import Process, Queue
from threading import Thread

from pikake.task import Task


class Browser(QWebView):

    refresh_signal = pyqtSignal()
    scroll_signal = pyqtSignal(bool)

    def __init__(self, url, display_time, refresh=False):
        super(QWebView, self).__init__()

        self.url = url
        self.refresh = refresh
        self.display_time = display_time

        self.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
        self.load(QUrl(url))
#        self.showFullScreen()
        

        self.refresh_signal.connect(self.reload_page)
        self.scroll_signal.connect(self.scroll)

        self.page().mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOn)
        self.page().mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOn)

    def reload_page(self):
        self.load(QUrl(self.url))

    def get_attrs(self):
        values = {}
        values['url'] = self.url
        values['display_time'] = self.display_time
        values['refresh'] = self.refresh
        return values

    def scroll(self, down):
        if down:
            self.page().mainFrame().scroll(0,1)
        else:
            self.page().mainFrame().scroll(0, -1)


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

                    browser.page().mainFrame().scroll(100,100)

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

        self.scroll_thread = Thread(target=self.scrolling_thread, args=(self.browser,))
        self.scroll_thread.start()

        self.browser_app.exec_()

    def scrolling_thread(self, browser):
        self.must_run = True
        self.must_wait = False
        down = True
        mainFrame = browser.page().mainFrame()
        while self.must_run:
            while not self.must_wait and self.must_run:
                time.sleep(0.03)
                min_ = mainFrame.scrollBarMinimum(Qt.Vertical)
                max_ = mainFrame.scrollBarMaximum(Qt.Vertical)
                pos = mainFrame.scrollBarValue(Qt.Vertical)
                if pos == max_:
                    down = False
                elif pos == min_:
                    down = True
                browser.scroll_signal.emit(down)
