#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json

from PyQt4.QtGui import QApplication

from browser import *

from flask import Flask
from flask import render_template
from flask import request
from threading import Thread

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

def launch_browser():
    data = json.load(open('./config.json', 'r'))

    browser_app = QApplication(sys.argv)
     
    browser = Browser()
    browser.set_urls(data['tabs'])
    browser.start()
    browser.show()

    browser_app.exec_()

if __name__ == '__main__':
    browser_thread = Thread(target = launch_browser)
    browser_thread.start()

    app.run()
