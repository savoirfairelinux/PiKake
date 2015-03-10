#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
import signal
import logging

from multiprocessing import Process, Queue
from flask import Flask
from flask import render_template
from flask import request

from pikake.browser import *
from pikake.manager import Manager
from pikake.task import Task


pikake_dir = os.path.dirname(os.path.abspath(__file__))
cfg = {}

app = Flask(__name__)
manager = Manager()


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', config=cfg)


@app.route('/', methods=['POST'])
def post():
    cfg['tabs'] = [tab for tab in filter(None, request.form.getlist('option[]'))]
    task = Task()
    task.type = 'save_config'
    task.value = cfg['tabs']
    manager.task_queue.put(task)
    return "New tabs saved"


def main():

    def signal_handler(signal, frame):
        logging.debug('You pressed Ctrl+C!')
        manager.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    manager.start()
    app.run()


if __name__ == '__main__':
    main()
