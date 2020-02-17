import logging
import queue
import threading

from time import sleep
from .rdap_input import RDAPInput
from .rdap_query_worker import RDAPQueryWorker
from .rdap_save_worker import RDAPSaveWorker


class RDAPManager(threading.Thread):
    '''
    Manager thread that is responsible for managing the RDAP crawl.
    '''

    def __init__(self, config):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger("SpiderRDAP").getChild("RDAPManager")
        self.proxy_list = list(config.proxy_list.read().splitlines())
        """
        Input Queue is left unbounded because of potential for
        deadlock since RDAPQueryWorker tries to reinsert elements in queue.
        However, we try to get input_thread to respect maxsize=3 * config.workers
        """
        self.input_queue = queue.Queue()
        self.input_threads = [RDAPInput(self, config)]
        self.save_queue = queue.Queue()
        self.save_threads = [RDAPSaveWorker(
            self, config, self.save_queue) for i in range(0, config.workers)]
        self.worker_threads = [RDAPQueryWorker(
            self, self.proxy_list, self.input_queue, self.save_queue) for i in range(0, config.workers)]

        self.stats = {
            'skipped': 0,
            'failed': 0,
            'in_progress': 0,
            'done': 0,
            'tld_unsupported': 0
        }

    def run(self):
        self.logger.info('Starting threads...')
        list(map(lambda thread: thread.start(), self.input_threads))
        self.logger.debug(self.input_queue.qsize())
        sleep(1)
        list(map(lambda thread: thread.start(), self.worker_threads))
        list(map(lambda thread: thread.start(), self.save_threads))
        self.logger.info('All threads started')
        while self.saveThreadsAlive():
            self.logger.info(self.stats)
            self.logger.debug("Worker Threads Alive: {}".format(
                self.workerThreadsAlive()))
            self.logger.debug("Save Threads Alive: {}".format(
                self.saveThreadsAlive()))
            sleep(5)
        self.logger.info(self.stats)

    def inputThreadsAlive(self):
        return any(map(lambda thread: thread.is_alive(), self.input_threads))

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
