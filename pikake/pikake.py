#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import time

from multiprocessing import Process, Queue

from pikake.browser import *
from pikake.manager import Manager
import pikake.config

def main():
    queue = Queue()

    for i in range(3):
        queue.put(Task('load_url', 'http://kaji:kaji@demo.kaji-project.org/grafana'))

    manager = Manager(queue)
    manager.run()


if __name__ == '__main__':
    main()
