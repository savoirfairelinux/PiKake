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
import pikake.auth


pikake_dir = os.path.dirname(os.path.abspath(__file__))

import json
from jinja2 import Environment, PackageLoader

app = Flask(__name__)


@app.route('/', methods=['GET'])
@auth.requires_auth
def index():
    with open(app.config['configfile'], 'r') as f:
        cfg = json.load(f)
    return render_template('index.html', config=cfg['tabs'])


@app.route('/', methods=['POST'])
@auth.requires_auth
def post():
    tab_ids = set([x.split("__")[-1] for x in request.form.keys() if x.split("__")[-1]])
    tab_ids = sorted(list(tab_ids))

    with open(app.config['configfile'], 'r') as f:
        cfg = json.load(f)

    cfg['tabs'] = []

    for tab_id in tab_ids:
        tab = {}
        tab['url'] = request.form.get("url__" + tab_id, None)

        if not tab['url']:
            continue

        tab['display_time'] = int(request.form.get("display_time__" + tab_id, 0))
        tab['refresh'] = True if request.form.get("refresh__" + tab_id, False) else False
        tab['autoscroll'] = True if request.form.get("vertical__" + tab_id, False) else False
        cfg['tabs'].append(tab)

    task = Task()
    task.type = 'save_config'
    task.value = cfg
    app.manager.task_queue.put(task)

    return redirect(url_for("index"))


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

    # Uses defaults credentials if config file not found
    if os.path.isfile(app.config['configfile']):
        pikake.auth.load_credentials(app.config['configfile'])

    signal.signal(signal.SIGINT, signal_handler)
    manager = Manager(app)
    manager.start()
    app.manager = manager
    app.run()


if __name__ == '__main__':
    main()
