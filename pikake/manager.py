# -*- coding: utf-8 -*-

import logging
import time

from threading import Thread
from multiprocessing import Process, Queue

from pikake.browser import BrowserProcess, Browser

class Manager(Thread):

    def __init__(self, tasks = Queue()):
        super(Thread, self).__init__()
        self.tasks = tasks
        self.is_running = False
        self.browser_processes = []

    def accomplish(self, task):
        if task.type == "load_url":
            browser_process = BrowserProcess(task.value)
            self.browser_processes.append(browser_process)
            browser_process.start()

    def shutdown(self):
        logging.debug("Stopping Manager")
        self.is_running = False

    def run(self):
        self.is_running = True
        logging.debug("Starting Manager")

        while self.is_running:
            time.sleep(0.1)
            if not self.tasks.empty():
                logging.debug("Task received")
                task = self.tasks.get()
                self.accomplish(task)

