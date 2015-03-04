#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
import signal
import logging

from multiprocessing import Process, Queue

from pikake.browser import *
from pikake.manager import Manager
import pikake.config

def main():

    queue = Queue()
    value1 = { 'url': 'http://kaji:kaji@demo.kaji-project.org/grafana',
                  'display_time' : 10,
                  'refresh': False }

    value2 = { 'url': 'http://www.google.ca',
                  'display_time' : 10,
                  'refresh': False }

    queue.put(Task('load_url', value1))
    queue.put(Task('load_url', value2))


    manager = Manager(queue)

    def signal_handler(signal, frame):
        logging.debug('You pressed Ctrl+C!')
        manager.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    manager.run()


if __name__ == '__main__':
    main()
