import json
import logging
import queue
import threading
import time


class RDAPSaveWorker(threading.Thread):

    def __init__(self, manager, config, save_queue, custom_config):
        threading.Thread.__init__(self)
        logger_name = custom_config.get("logger_name", "SpiderRDAP")
        self.logger = logging.getLogger(
            logger_name).getChild("RDAPSaveWorker")
        self.save_path = config.save_path
        self.save_file = open('{}/rdap_{}.txt'.format(self.save_path, int(time.time())), 'a')
        self.manager = manager
        self.save_queue = save_queue
        self.error_file = custom_config.get("error_file", "error_common")

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
                f = open('{}/{}.txt'.format(self.save_path, self.error_file), 'a')
                f.write('{}\n'.format(rdap_data['domain']))
                f.close()

            self.logger.debug("Save Queue Size: {}".format(
                self.save_queue.qsize()))
            self.logger.debug("Marking task done!")
            self.save_queue.task_done()

        self.save_file.close()

    def save_data(self, rdap_data):
        json.dump(rdap_data['data'], self.save_file)
        self.save_file.write('\n')
