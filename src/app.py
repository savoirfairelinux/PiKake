#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json

from PyQt4.QtGui import QApplication

from browser import *

from flask import Flask
from flask import render_template
from flask import request
from multiprocessing import Process

import os
import time
import config

pikake_dir = os.path.dirname(os.path.abspath(__file__))
cfg = {}

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', config=cfg)


@app.route('/', methods=['POST'])
def post():
    cfg['tabs'] = filter(None, request.form.getlist('option[]'))
    config.save_config(pikake_dir, cfg)
    return "New tabs saved"

def launch_browser(url):

    browser_app = QApplication(sys.argv)
     
    browser = Browser(url)

    browser.start()
    browser.show()

    browser_app.exec_()

if __name__ == '__main__':
    p1 = Process(target = launch_browser, args = ('http://www.google.ca',))
    p2 = Process(target = launch_browser, args = ('http://www.radio-canada.ca',))
    p3 = Process(target = launch_browser, args = ('http://www.lapresse.ca',))

    p1.start()
    p2.start()
    p3.start()

    #print(p2)
    #print(p3)

    #app.run()
