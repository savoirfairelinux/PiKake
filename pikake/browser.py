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
import pikake.pikake


class Browser(QWebView):

    refresh_signal = pyqtSignal()
    scroll_signal = pyqtSignal(bool)

    def __init__(self, url, display_time, refresh=False, autoscroll=True):
        super(QWebView, self).__init__()

        self.url = url
        self.refresh = refresh
        self.display_time = display_time
        self.autoscroll = autoscroll

        self.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)

        # CSS needed to hide scrollbar
        style_url = 'file://' + pikake.pikake.pikake_dir + '/assets/css/style.css'
        self.settings().setUserStyleSheetUrl(QUrl(style_url))

        self.load(QUrl(url))
        self.showFullScreen()

        self.refresh_signal.connect(self.reload_page)
        self.scroll_signal.connect(self.scroll)

        self.mainFrame = self.page().mainFrame()
        self.mainFrame.setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAsNeeded)
        self.mainFrame.setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAsNeeded)

        self.must_run = True
        self.must_wait = False if self.autoscroll else True

    def reload_page(self):
        self.load(QUrl(self.url))

    def get_attrs(self):
        values = {}
        values['url'] = self.url
        values['display_time'] = self.display_time
        values['refresh'] = self.refresh
        values['autoscroll'] = self.autoscroll
        return values

    def scroll(self, down):
        if down:
            self.mainFrame.scroll(0, 1)
        else:
            self.mainFrame.scroll(0, -1)

    def resume_scrolling(self):
        self.must_wait = False

    def pause_scrolling(self):
        self.must_wait = True


class BrowserProcess(Process):

    def __init__(self, url, display_time, refresh=False, autoscroll=True):
        super(Process, self).__init__()
        self.url = url
        self.display_time = display_time
        self.refresh = refresh
        self.autoscroll = autoscroll
        self.browser = None
        self.queue = Queue()
        self.response_queue = Queue()

    def command_thread(self):
        while True:
            time.sleep(0.1)
            if not self.queue.empty():
                command = self.queue.get()

                if command == 'show':
                    self.browser.setFocus()
                    self.browser.activateWindow()
                    self.browser.mainFrame.setScrollBarValue(Qt.Vertical, 0)

                elif command == 'get_attrs':
                    attrs = self.browser.get_attrs()
                    self.response_queue.put(attrs)

                elif command == 'reload':
                    if self.browser.refresh:
                        self.browser.refresh_signal.emit()

                elif command == 'pause_scrolling':
                    self.browser.pause_scrolling()

                elif command == 'resume_scrolling':
                    if self.browser.autoscroll:
                        self.browser.resume_scrolling()

    def scrolling_thread(self):
        down = True

        mainFrame = self.browser.mainFrame

        while self.browser.must_run:
            while not self.browser.must_wait and self.browser.must_run:
                time.sleep(0.03)

                pos = mainFrame.scrollBarValue(Qt.Vertical)
                min_ = mainFrame.scrollBarMinimum(Qt.Vertical)
                max_ = mainFrame.scrollBarMaximum(Qt.Vertical)

                if pos == max_:
                    down = False
                elif pos == min_:
                    down = True

                self.browser.scroll_signal.emit(down)

    def run(self):
        self.browser_app = QApplication(sys.argv)
        self.browser = Browser(self.url, self.display_time, self.refresh, self.autoscroll)
        self.browser.show()

        t = Thread(target=self.command_thread)
        t.start()

        self.scroll_thread = Thread(target=self.scrolling_thread)
        self.scroll_thread.start()

        self.browser_app.exec_()
