#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import signal
import logging
import argparse

from multiprocessing import Process, Queue
from flask import Flask
from flask import render_template
from flask import request, redirect, url_for

from pikake.manager import Manager
import pikake.webserver


pikake_dir = os.path.dirname(os.path.abspath(__file__))

config = {}

def main():
    # Handle args
    parser = argparse.ArgumentParser(description='Pikake')
    parser.add_argument('--config', '-c', dest='configfile',
                        default=os.path.join(os.path.dirname(__file__), 'config.json'),
                        help='config file')
    parser.add_argument('--debug', '-d', dest='debug',
                        default=False, action='store_true',
                        help='debug mode')
    args = parser.parse_args()

    app = pikake.webserver.app
    # Set config file
    app.config['configfile'] = config['configfile'] = args.configfile
    app.config['debug'] = config['debug'] = args.debug

    def signal_handler(signal, frame):
        logging.debug('You pressed Ctrl+C!')
        manager.shutdown()
        sys.exit(0)

    # Uses defaults credentials if config file not found
    if os.path.isfile(app.config['configfile']):
        auth.load_credentials(app.config['configfile'])

    signal.signal(signal.SIGINT, signal_handler)
    manager = Manager(app)
    manager.start()
    app.manager = manager
    app.run()


if __name__ == '__main__':
    main()
