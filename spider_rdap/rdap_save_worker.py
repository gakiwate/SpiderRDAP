import json
import logging
import queue
import threading
import time


class RDAPSaveWorker(threading.Thread):

    def __init__(self, manager, config, save_queue):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(
            "SpiderRDAP").getChild("RDAPSaveWorker")
        self.save_path = config.save_path
        self.manager = manager
        self.save_queue = save_queue

    def run(self):
        while self.manager.workerThreadsAlive() or not self.save_queue.empty():
            try:
                rdap_data = self.save_queue.get(block=False, timeout=5)
            except queue.Empty:
                time.sleep(1)
                continue

            if rdap_data['error'] is None:
                self.save_data(rdap_data)
            else:
                f = open('{}/error.txt'.format(self.save_path), 'a')
                f.write('{}\n'.format(rdap_data['data']))
                f.close()

    def save_data(self, rdap_data):
        json_file = '{}/{}_{}.json'.format(self.save_path,
                                           rdap_data['domain'], rdap_data['timestamp'])
        with open(json_file, 'w') as f:
            json.dump(rdap_data['data'], f)
