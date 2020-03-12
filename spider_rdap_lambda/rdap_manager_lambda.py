import boto3
import json
import logging
import queue
import threading

from concurrent.futures import ThreadPoolExecutor
from math import ceil
from time import sleep

from .rdap_input_lambda import RDAPInputLambda
from .rdap_save_worker_lambda import RDAPSaveWorkerLambda
from .rdap_query_worker_lambda import RDAPQueryWorkerLambda


class RDAPManagerLambda(threading.Thread):
    '''
    Manager thread that is responsible for managing the RDAP crawl.
    '''

    def __init__(self, config):
        threading.Thread.__init__(self)
        logger_name = config.logger_name
        if logger_name == None:
            logger_name = "SpiderRDAPLambda"
        self.logger = logging.getLogger(
            logger_name).getChild("RDAPManagerLambda")
        self.logger.debug("Logger Name: {}".format(logger_name))
        self.region = config.region
        self.logger.info(
            'Initializing Manager for region: {}'.format(self.region))
        self.save_path = config.save_path
        self.lambda_ips = []
        """
        Input Queue is left unbounded because of potential for deadlock
        """
        self.input_queue = queue.Queue()
        self.inputter = RDAPInputLambda(self, config.domain_list)
        self.save_queue = queue.Queue()
        self.lambda_workers = config.lambda_workers

        self.stats = {
            'skipped': 0,
            'failed': 0,
            'in_progress': 0,
            'done': 0,
            'tld_unsupported': 0
        }

    def run(self):
        self.logger.info('Starting Manager')
        try:
            self.logger.info('Enqueing {} domains'.format(self.lambda_workers))
            self.inputter.enqueueDomainBatch(self.lambda_workers)
        except Exception as e:
            self.logger.info("Exception when enqueing {}".format(e))

        self.save_threads = [RDAPSaveWorkerLambda(
            self, self.save_path, self.save_queue) for i in range(0, ceil(self.lambda_workers / 100))]
        self.worker_threads = [RDAPQueryWorkerLambda(
            self, self.region, self.input_queue, self.save_queue) for i in range(0, self.lambda_workers)]

        self.logger.info('Starting threads...')
        with ThreadPoolExecutor(max_workers=len(self.worker_threads)) as executor:
            executor.map(
                lambda thread: thread.start(), self.worker_threads)
            executor.map(
                lambda thread: thread.start(), self.save_threads)

        while self.saveThreadsAlive():
            self.logger.info(self.stats)
            sleep(5)
            self.logger.debug("Worker Threads Alive: {}".format(
                self.workerThreadsAlive()))
            self.logger.debug("Save Threads Alive: {}".format(
                self.saveThreadsAlive()))

        self.logger.info(self.stats)
        self.logger.info(self.lambda_ips)

    def workerThreadsAlive(self):
        return any(map(lambda thread: thread.is_alive(), self.worker_threads))

    def saveThreadsAlive(self):
        return any(map(lambda thread: thread.is_alive(), self.save_threads))

    def incrTLDUnsupported(self):
        self.stats['tld_unsupported'] += 1

    def incrSkipped(self):
        self.stats['skipped'] += 1

    def incrFailed(self):
        self.stats['failed'] += 1

    def decrInProgress(self):
        self.stats['in_progress'] -= 1

    def incrInProgress(self):
        self.stats['in_progress'] += 1

    def incrDone(self):
        self.stats['done'] += 1


if __name__ == "__main__":
    pass
