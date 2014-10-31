import threading
import gobject
import uzbl_tabbed as uzbl


class UzblBrowser(threading.Thread):

    def __init__(self):
        gobject.threads_init()
        threading.Thread.__init__(self)
        self.browser = uzbl.UzblTabbed()

    def run(self):
        self.browser.run()

browser_thread = UzblBrowser()