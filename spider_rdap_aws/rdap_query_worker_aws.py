import json
import logging
import queue
import threading
import time
import random
import xmlrpc.client


class RDAPQueryWorkerAWS(threading.Thread):

    def __init__(self, manager, host, port, input_queue, save_queue):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(
            "SpiderRDAPAWS").getChild("RDAPQueryWorkerAWS")
        self.manager = manager
        self.input_queue = input_queue
        self.save_queue = save_queue
        self.rpc_client = self.setup_connection(host, port)

    def setup_connection(self, host, port):
        target_url = 'http://{}:{}'.format(str(host), str(port))
        self.logger.info(
            "Setting up RPC Client at {}".format(target_url))
        client = xmlrpc.client.ServerProxy(target_url)
        return client

    def run(self):
        while not self.input_queue.empty():
            self.logger.debug("Save Queue Size: {}".format(
                self.save_queue.qsize()))
            try:
                rdap_work_info = self.input_queue.get(block=False, timeout=5)
                self.logger.debug(rdap_work_info)
            except queue.Empty:
                self.logger.info(
                    "Input Queue Empty!")
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
                """
                If 3 attempts we declare failure!
                """
                if rdap_work_info['attempt'] >= 3:
                    self.manager.incrFailed()
                    self.manager.incrSkipped()
                    self.save_queue.put(
                        {'error': 'skipped', 'data': rdap_work_info, 'domain': domain, 'timestamp': timestamp})
                else:

                    rdap_work_info['attempt'] += 1
                    self.logger.info(
                        "Failed attempt: {}".format(rdap_work_info))
                    """
                    Potential for deadlock if the input queue is full.
                    For now, we get around this by keeping the input
                    queue unbouded but limiting the input_thread to
                    keep upto 3 * workers items in the input_queue
                    """
                    self.input_queue.put(rdap_work_info)

            else:  # return_code == 'tld_rdap_unsupported'
                self.manager.incrTLDUnsupported()
                self.save_queue.put(
                    {'error': 'tld_unsupported', 'data': rdap_work_info, 'domain': domain, 'timestamp': timestamp})

            self.logger.debug("Marking task done!")
            self.input_queue.task_done()
            time.sleep(random.uniform(0, 1))

    def rdap_query(self, rdap_work_info):
        domain = rdap_work_info["domain"]
        if len(rdap_work_info["rdap_url"]) == 0:
            return 'tld_rdap_unsupported', None
        rdap_url = rdap_work_info["rdap_url"][rdap_work_info['attempt'] % len(
            rdap_work_info["rdap_url"])]
        query_url = "{}/domain/{}".format(rdap_url, domain)
        self.logger.debug(
            "Starting RPC Request: {}".format(query_url))

        json_rdap_data = None
        try:
            return_code, json_rdap_data = self.rpc_client.queryRDAP(query_url)
        except Exception as e:
            return 'failed', e

        return return_code, json_rdap_data


if __name__ == "__main__":
    pass
