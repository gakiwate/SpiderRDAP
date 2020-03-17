import json
import logging
import queue
import requests
import threading

from collections import defaultdict
from time import sleep


class RDAPInput(threading.Thread):
    '''
    RDAPInput Thread
    '''

    def __init__(self, manager, config, custom_config):
        threading.Thread.__init__(self)
        logger_name = custom_config.get("logger_name", "SpiderRDAP")
        self.logger = logging.getLogger(logger_name).getChild("RDAPInput")
        self.manager = manager
        self.domain_list = config.domain_list
        """
        input queue has no maxsize when created to avoid deadlocks.
        but we try to get input_thread to respect the maxsize limit
        maybe try to come up with a better fix
        """
        self.maxsize = 3 * config.workers
        self.input_queue = self.manager.input_queue
        self.rdap_tld_bootstrap = self.rdap_bootstrap()

    def rdap_bootstrap(self):
        rdap_tld_bootstrap = defaultdict(list)
        r = requests.get("https://data.iana.org/rdap/dns.json")
        r = json.loads(r.text)
        for itm in r["services"]:
            for tld in itm[0]:
                rdap_tld_bootstrap[tld].extend(itm[1])
        return rdap_tld_bootstrap

    def construct_query(self, domain):
        rdap_query = {}
        rdap_query['attempt'] = 0
        rdap_query['domain'] = domain
        tld = domain.split('.')[-1].lower()
        rdap_query['rdap_url'] = self.rdap_tld_bootstrap.get(tld, [])
        return rdap_query

    def run(self):
        for domain in self.domain_list:
            domain = domain.strip()
            rdap_query = self.construct_query(domain)
            queue_full = True
            while queue_full:
                try:
                    if self.input_queue.qsize() > self.maxsize:
                        raise queue.Full
                    self.input_queue.put(rdap_query, block=True, timeout=5)
                    queue_full = False
                except queue.Full:
                    sleep(1)
                    queue_full = True
                    self.logger.info(
                        "Queue Full, Maybe increase number of worker threads!")
                    self.logger.debug(
                        "Queue Full, Trying to put {} in queue again".format(domain))
                    self.logger.debug(
                        "Input Queue Size: {}".format(self.input_queue.qsize()))


if __name__ == "__main__":
    pass
