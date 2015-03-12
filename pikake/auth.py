#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from functools import wraps
from flask import request, Response


username_ = 'admin'
password_ = 'admin'


def check_auth(username, password):
    """This function is called to check if a username / password combination is valid."""
    return username == username_ and password == password_


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def save_credentials(username, password, file_name):
    with open(file_name, 'r') as f:
        cfg = json.load(f)

    cfg['credentials'] = {'username': username, 'password': password}

    with open(file_name, 'w') as f:
        json.dump(cfg, f, sort_keys=True, indent=4)


def load_credentials(file_name):
    global username_
    global password_

    with open(file_name, 'r') as f:
        cfg = json.load(f)
        creds = cfg['credentials']
        username_ = creds['username']
        password_ = creds['password']
