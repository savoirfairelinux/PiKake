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

    def __init__(self, app, tasks=Queue()):
        # TODO Ask Gstark
        Thread.__init__(self)
        self.app = app
        self.task_queue = tasks
        self.is_running = False
        self.browser_processes = {}
        self.browser_id_seq = []

        self.display_time = 0
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

            # Replace process at given index
            if "index" in task.value.keys():
                i = task.value['index']
                del self.browser_id_seq[i]
                self.browser_id_seq.insert(i, pid)
            else:
                self.browser_id_seq.append(pid)

            if self.display_time == 0:
                self.display_time = task.value['display_time']

        elif task.type == 'save_config':
            self.save_config(task.value)
            self.load_config()

        elif task.type == 'get_config':
            pass

    def save_config(self, config):
        with open(self.app.config['configfile'], 'w') as f:
            json.dump(config, f)

    def load_config(self):
        with open(self.app.config['configfile'], 'r') as f:
            cfg = json.load(f)

            i = 0
            new_tabs = cfg['tabs']

            max_index = max(len(new_tabs), len(self.browser_id_seq))

            for i in range(max_index):
                task = Task()

                # New config has more tabs than current config
                # Load all remaining tabs from new config
                if i >= len(self.browser_id_seq):
                    task.type = 'load_url'
                    task.value = new_tabs[i]
                    self.task_queue.put(task)
                    continue

                pid = self.browser_id_seq[i]
                proc = self.browser_processes.get(pid)

                # Current config has more tabs than the new config
                # Kill all remaining browser processes
                if i >= len(new_tabs):
                    proc.terminate()
                    continue

                proc.queue.put('get_attrs')
                attrs = proc.response_queue.get(True)

                # New config tab differs from current tab
                # Kill current process and replace it by the new one at same index
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

    def display_time_is_over(self):
        return (self.display_time + self.reference_time) <= time.time()

    def load_next_browser(self):
        self.current_browser_index = self.next_browser_index()
        browser_proc = self.browser_processes[self.browser_id_seq[self.current_browser_index]]
        browser_proc.queue.put('show')
        self.display_time = browser_proc.display_time

        self.refresh_browser(self.next_browser_index())

    def refresh_browser(self, index):
        browser_proc = self.browser_processes[self.browser_id_seq[index]]
        browser_proc.queue.put('reload')

    def next_browser_index(self):
        return (self.current_browser_index + 1) % len(self.browser_id_seq)

    def run(self):
        self.is_running = True
        logging.debug("Starting Manager")

        while self.is_running:
            time.sleep(0.1)

            if not self.task_queue.empty():
                logging.debug("Task received")
                task = self.task_queue.get()
                self.accomplish(task)

            if self.display_time_is_over():
                self.reset_timer()
                self.load_next_browser()
