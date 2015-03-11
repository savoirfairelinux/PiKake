#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
import signal
import logging
import argparse

from multiprocessing import Process, Queue
from flask import Flask
from flask import render_template
from flask import request, redirect, url_for

from pikake.browser import *
from pikake.manager import Manager
from pikake.task import Task


pikake_dir = os.path.dirname(os.path.abspath(__file__))

import json
from jinja2 import Environment, PackageLoader

app = Flask(__name__)




@app.route('/', methods=['GET'])
def index():
    with open(app.config['configfile'], 'r') as f:
        cfg = json.load(f)
    return render_template('index.html', config=cfg)


@app.route('/', methods=['POST'])
def post():
    tab_ids = set([x.split("__")[-1] for x in request.form.keys() if x.split("__")[-1]])
    tab_ids = sorted(list(tab_ids))
    tabs = []
    for tab_id in tab_ids:
        tab = {}
        tab['url'] = request.form.get("url__" + tab_id, None)
        if tab['url'] is None:
            continue
        tab['display_time'] = int(request.form.get("display_time__" + tab_id, 0))
        tab['refresh'] = True if request.form.get("refresh__" + tab_id, False) else False
        tab['vertical'] = True if request.form.get("vertical__" + tab_id, False) else False
        tabs.append(tab)
    task = Task()
    task.type = 'save_config'
    task.value = tabs
    app.manager.task_queue.put(task)
    return redirect('/')


def main():
    # Handle args
    parser = argparse.ArgumentParser(description='Pikake')
    parser.add_argument('--config', '-c', dest='configfile',
                        default=os.path.join(os.path.dirname(__file__), 'config.json'),
                         help='config file')
    args = parser.parse_args()
    # Set config file
    app.config['configfile'] = args.configfile

    def signal_handler(signal, frame):
        logging.debug('You pressed Ctrl+C!')
        manager.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    manager = Manager(app)
    manager.start()
    app.manager = manager
    app.run()


if __name__ == '__main__':
    main()
