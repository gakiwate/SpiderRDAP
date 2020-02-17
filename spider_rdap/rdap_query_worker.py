import json
import logging
import queue
import threading
import time
import requests


class RDAPQueryWorker(threading.Thread):

    def __init__(self, manager, input_queue, save_queue):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(
            "SpiderRDAP").getChild("RDAPQueryWorker")
        self.manager = manager
        self.input_queue = input_queue
        self.save_queue = save_queue

    def run(self):
        while self.manager.inputThreadsAlive() or not self.input_queue.empty():
            self.logger.debug("Save Queue Size: {}".format(
                self.save_queue.qsize()))
            try:
                rdap_work_info = self.input_queue.get(block=False, timeout=5)
                self.logger.debug(rdap_work_info)
            except queue.Empty:
                self.logger.info(
                    "Input Queue Empty! Maybe increase number of Input Threads!")
                time.sleep(1)
                continue

            self.manager.incrInProgress()
            domain = rdap_work_info["domain"]
            return_code, json_rdap_data = self.rdap_query(rdap_work_info)
            self.manager.decrInProgress()

            timestamp = time.time()
            if return_code == 'done':
                self.manager.incrDone()
                self.save_queue.put(
                    {'error': None, 'data': json_rdap_data, 'domain': domain, 'timestamp': timestamp})
            elif return_code == 'failed':

                rdap_work_info['attempt'] += 1

                if rdap_work_info['attempt'] > 3:
                    self.manager.incrFailed()
                    self.manager.incrSkipped()
                    self.save_queue.put(
                        {'error': 'skipped', 'data': rdap_work_info})
                else:
                    self.input_queue.put(rdap_work_info)
            else:  # return_code == 'tld_rdap_unsupported'
                self.manager.incrTLDUnsupported()
                self.save_queue.put(
                    {'error': 'tld_unsupported', 'data': rdap_work_info})

            self.input_queue.task_done()

    def rdap_query(self, rdap_work_info):
        domain = rdap_work_info["domain"]
        if len(rdap_work_info["rdap_url"]) == 0:
            return 'tld_rdap_unsupported', None
        rdap_url = rdap_work_info["rdap_url"][rdap_work_info['attempt'] % len(
            rdap_work_info["rdap_url"])]
        query_url = "{}/domain/{}".format(rdap_url, domain)
        proxies = rdap_work_info["proxies"]

        try:
            r = requests.get(query_url, proxies=proxies, timeout=10)
        except Exception as e:
            return 'failed', e
        json_rdap_data = None
        if r.status_code == 200:
            return_code = 'done'
            json_rdap_data = json.loads(r.text)
        else:
            return_code = 'failed'
            self.logger.debug(json_rdap_data)

        return return_code, json_rdap_data


if __name__ == "__main__":
    pass
