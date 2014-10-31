import threading
import time


class Caroussel(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.browser = None
        self.running = True
        self.tick = 10

    def run(self):
        while self.running:
            time.sleep(self.tick)
            self.browser.next_tab()

caroussel = Caroussel()