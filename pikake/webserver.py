#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json

from flask import Flask
from flask import render_template
from flask import request, redirect, url_for
from jinja2 import Environment, PackageLoader

from pikake.manager import Manager
from pikake.task import Task
import pikake.auth


pikake_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)


@app.route('/', methods=['GET'])
@pikake.auth.requires_auth
def index():
    with open(app.config['configfile'], 'r') as f:
        cfg = json.load(f)
    return render_template('index.html', config=cfg['tabs'])


@app.route('/', methods=['POST'])
@pikake.auth.requires_auth
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
