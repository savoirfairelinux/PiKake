#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json

from flask import Flask, flash
from flask import render_template
from flask import request, redirect, url_for
from jinja2 import Environment, PackageLoader

from pikake.manager import Manager
from pikake.task import Task
from pikake.utils import get_ips
import pikake.auth


pikake_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "Nieh4roT1oocuati1eej"


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

    flash('Configuration saved', 'success')

    return redirect(url_for("index"))


@app.route('/info', methods=['GET'])
def info():
    with open(app.config['configfile'], 'r') as f:
        cfg = json.load(f)
    ips = get_ips()
    host_ip_port = request.host.split(":")
    host_ip = host_ip_port[0]
    host_port = None
    if len(host_ip_port) == 2:
        host_port = host_ip_port[1]
    # Clean data
    if host_ip not in ips:
        cfg['credentials']['password'] = "*******"
    if host_port is not None:
        ips = [":".join((ip, host_port)) for ip in ips]
    return render_template('info.html', config=cfg, ips=ips)

@app.route('/admin', methods=['GET', 'POST'])
@pikake.auth.requires_auth
def admin():
    if request.method == 'POST':
        if request.form.get("password") and request.form.get("username"):
            pikake.auth.save_credentials(request.form.get("username"),
                                         request.form.get("password"),
                                         app.config['configfile'])
            flash('Credentials saved', 'success')
        else:
            flash('Credentials NOT saved', 'danger')
        return redirect(url_for("admin"))
    else:
        with open(app.config['configfile'], 'r') as f:
            cfg = json.load(f)
        ips = get_ips()
        return render_template('admin.html', config=cfg, ips=ips)

