#!flask/bin/python
from flask import Flask
from flask import render_template
from flask import request

import os
import time

import config
from browser import browser_thread
from caroussel import caroussel

pikake_dir = os.path.dirname(os.path.abspath(__file__))
cfg = config.load_config(pikake_dir)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', config=cfg)


@app.route('/', methods=['POST'])
def post():
    cfg['tabs'] = filter(None, request.form.getlist('option[]'))
    config.save_config(pikake_dir, cfg)
    reload_tabs()
    return "New tabs saved"


def reload_tabs():
    tn = len(browser_thread.browser.tabs)

    # Launch the browser
    for tab in cfg['tabs']:
        browser_thread.browser.new_tab(tab)

    # Close previously opened tabs
    for x in xrange(tn):
        time.sleep(2)
        browser_thread.browser.notebook.remove_page(0)

if __name__ == '__main__':
    # Start Uzbl
    browser_thread.start()
    time.sleep(2)
    reload_tabs()

    # Start the tab caroussel
    caroussel.browser = browser_thread.browser
    caroussel.start()

    # Start Flask
    app.run()
