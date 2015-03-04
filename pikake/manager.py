# -*- coding: utf-8 -*-

import logging
import time
import signal

from threading import Thread
from multiprocessing import Process, Queue

from pikake.browser import BrowserProcess, Browser

class Manager(Thread):

    def __init__(self, tasks = Queue()):
        super(Thread, self).__init__()
        self.tasks = tasks
        self.is_running = False
        self.browser_processes = {}
        self.browser_id_seq = []

        self.display_delay = 0
        self.reset_timer()
        self.current_browser_index = 0


    def accomplish(self, task):
        if task.type == "load_url":
            browser_process = BrowserProcess(task.value['url'], task.value['display_time'], task.value['refresh'])
            browser_process.start()
            pid = browser_process.pid
            self.browser_processes[pid] = browser_process
            self.browser_id_seq.append(pid)
            self.display_delay = task.value['display_time']

    def shutdown(self):
        logging.debug("Stopping Manager")
        self.is_running = False

        for key, value in self.browser_processes.items():
            value.terminate()

    def reset_timer(self):
        self.reference_time = time.time()

    def display_delay_is_over(self):
        return (self.display_delay + self.reference_time) <= time.time()

    def next_browser(self):
        self.current_browser_index = (self.current_browser_index + 1) % len(self.browser_id_seq)
        return self.browser_processes[self.browser_id_seq[self.current_browser_index]]

    def run(self):
        self.is_running = True
        logging.debug("Starting Manager")

        while self.is_running:
            time.sleep(0.1)

            if not self.tasks.empty():
                logging.debug("Task received")
                task = self.tasks.get()
                self.accomplish(task)

            if self.display_delay_is_over():
                self.reset_timer()
                browser = self.next_browser()
                browser.queue.put('show')
                self.display_time = browser.display_time
