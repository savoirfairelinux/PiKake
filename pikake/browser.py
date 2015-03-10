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

must_wait = False
must_run = True


def continue_scrolling():
    must_wait = False


def stop_scrolling(se):
    must_wait = True


def scrolling_thread(browser):
    must_run = True
    must_wait = False
    while must_run:
        while not must_wait and must_run:
            time.sleep(0.03)
            if browser.page() != None:
                if browser.page().mainFrame() != None:
                    if browser.ready:
                        browser.page().mainFrame().scroll(0,1)


class Browser(QWebView):

    refresh_signal = pyqtSignal()

    def __init__(self, url, display_time, refresh=False):
        super(QWebView, self).__init__()

        self.url = url
        self.refresh = refresh
        self.display_time = display_time
        self.ready = False

        self.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
        self.load(QUrl(url))
        #self.showFullScreen()

        self.refresh_signal.connect(self.reload_page)
        self.loadStarted.connect(self.not_read)
        self.loadFinished.connect(self.read)

        self.page().mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        self.page().mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)

    def read(self):
        print("READY")
        self.ready = True
        scroll_thread = Thread(target=scrolling_thread, args=(self,))

        scroll_thread.start()

    def not_read(self):
        print("NOT READY")
        self.ready = False

    def reload_page(self):
        print("RELOAD")
        self.reload()
        #self.load(QUrl(self.url))

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
                elif command == 'continue_scrolling':
                    #browser.continue_scrolling()
                    pass
                elif command == 'stop_scrolling':
                    #browser.stop_scrolling()
                    pass

    def run(self):
        self.browser_app = QApplication(sys.argv)
        self.browser = Browser(self.url, self.display_time, self.refresh)
        self.browser.show()

        t = Thread(target=self.command_thread, args=(self.browser,))
        t.start()



        self.browser_app.exec_()

