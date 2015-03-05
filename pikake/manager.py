# -*- coding: utf-8 -*-

import logging
import time
import os
import json

from threading import Thread
from multiprocessing import Process, Queue

from pikake.browser import BrowserProcess, Browser
from pikake.task import Task

class Manager(Thread):

    def __init__(self, tasks=Queue()):
        # TODO Ask Gstark 
        Thread.__init__(self)
        self.task_queue = tasks
        self.is_running = False
        self.browser_processes = {}
        self.browser_id_seq = []

        self.display_delay = 0
        self.reset_timer()
        self.current_browser_index = 0

        if self.task_queue.empty():
            self.load_config()

    def accomplish(self, task):
        if task.type == 'load_url':
            browser_process = BrowserProcess(task.value['url'], task.value['display_time'], task.value['refresh'])
            browser_process.start()
            pid = browser_process.pid
            self.browser_processes[pid] = browser_process

            # Replace process at index
            if "index" in task.value.keys():
                i = task.value['index']
                del self.browser_id_seq[i]
                self.browser_id_seq.insert(i, pid)
            else:
                self.browser_id_seq.append(pid)

            self.display_delay = task.value['display_time']

        elif task.type == 'save_config':
            #self.save_config(task.value)
            self.load_config()

        elif task.type == 'get_config':
            pass

    def save_config(self, config):
        with open(os.path.join(os.curdir, 'config.json'), 'w') as f:
            json.dump(config, f)

    def load_config(self):
        with open(os.path.join(os.curdir, 'config.json'), 'r') as f:
            cfg = json.load(f)

            i = 0
            new_tabs = cfg['tabs']
            max_index = max(len(new_tabs), len(self.browser_id_seq))

            for i in range(max_index):
                task = Task()

                if i >= len(self.browser_id_seq):
                    task.type = 'load_url'
                    task.value = new_tabs[i]
                    self.task_queue.put(task)
                    continue

                pid = self.browser_id_seq[i]
                proc = self.browser_processes.get(pid)

                if i >= len(new_tabs):
                    proc.terminate()
                    continue

                proc.queue.put('get_attrs')
                attrs = None

                while attrs is None:
                    attrs = proc.response_queue.get()

                if attrs != new_tabs[i]:
                    proc.terminate()

                    task.type = 'load_url'
                    task.value = new_tabs[i]
                    task.value['index'] = i

                    self.task_queue.put(task)

    def shutdown(self):
        logging.debug("Stopping Manager")
        self.is_running = False

        for value in self.browser_processes.values():
            value.terminate()

    def reset_timer(self):
        self.reference_time = time.time()

    def display_delay_is_over(self):
        return (self.display_delay + self.reference_time) <= time.time()

    def load_next_browser(self):
        self.current_browser_index = (self.current_browser_index + 1) % len(self.browser_id_seq)
        browser_proc = self.browser_processes[self.browser_id_seq[self.current_browser_index]]
        browser_proc.queue.put('show')
        self.display_time = browser_proc.display_time

    def run(self):
        self.is_running = True
        logging.debug("Starting Manager")

        while self.is_running:
            time.sleep(0.1)

            if not self.task_queue.empty():
                logging.debug("Task received")
                task = self.task_queue.get()
                self.accomplish(task)

            if self.display_delay_is_over():
                self.reset_timer()
                self.load_next_browser()
