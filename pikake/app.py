#!flask/bin/python
from flask import Flask
from flask import render_template
from flask import request

import config

import os
import subprocess
import shutil
import time

app = Flask(__name__)

pikake_dir = os.path.dirname(os.path.abspath(__file__))
cfg = config.load_config(pikake_dir)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', config=cfg)


@app.route('/', methods=['POST'])
def post():
    cfg['tabs'] = filter(None, request.form.getlist('option[]'))
    config.save_config(pikake_dir, cfg)
    reload_browser()
    return "New tabs saved"


def reload_browser():
    # Kill the browser
    os.system("pkill -9 -f firefox")
    os.system("pkill -9 -f iceweasel")

    # Reset the browser config
    shutil.rmtree("/home/pi/.mozilla", ignore_errors=True)
    shutil.copytree(
        os.path.join(pikake_dir, '.mozilla'),
        "/home/pi/.mozilla"
    )

    # Launch the browser
    for tab in cfg['tabs']:
        subprocess.Popen(
            'firefox -new-tab ' + tab,
            shell=True, stdin=None, stdout=None, stderr=None
        )
        time.sleep(10)


if __name__ == '__main__':
    reload_browser()
    app.run('0.0.0.0', debug=True)
