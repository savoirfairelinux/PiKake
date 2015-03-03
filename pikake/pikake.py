#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json

from PyQt5.Qt import QApplication

from pikake.browser import *

from multiprocessing import Process

import os
import time
import pikake.config

def launch_browser(url):

    browser_app = QApplication(sys.argv)
     
    browser = Browser(url)

#     browser.start()
    browser.show()

    browser_app.exec_()

def main():
    p1 = Process(target = launch_browser, args = ('http://kaji:kaji@demo.kaji-project.org/grafana',))
    p2 = Process(target = launch_browser, args = ('http://kaji:kaji@demo.kaji-project.org/grafana',))
    p3 = Process(target = launch_browser, args = ('http://kaji:kaji@demo.kaji-project.org/grafana',))
#     p2 = Process(target = launch_browser, args = ('http://www.google.ca',))

    p1.start()
    p2.start()
    p3.start()
#     p2.start()



if __name__ == '__main__':
    main()
