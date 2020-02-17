import json
import logging
import queue
import requests
import threading

from collections import defaultdict
from random import choice
from time import sleep


class RDAPInput(threading.Thread):
    '''
    RDAPInput Thread
    '''

    def __init__(self, manager, config):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger("SpiderRDAP").getChild("RDAPInput")
        self.manager = manager
        self.proxy_list = list(config.proxy_list.read().splitlines())
        self.domain_list = config.domain_list
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
        tld = domain.split('.')[-1]
        rdap_query['rdap_url'] = self.rdap_tld_bootstrap.get(tld, [])
        random_proxy = choice(self.proxy_list)
        rdap_query['proxies'] = {'http': random_proxy, 'https': random_proxy}
        return rdap_query

    def run(self):
        for domain in self.domain_list:
            domain = domain.strip()
            rdap_query = self.construct_query(domain)
            queue_full = True
            while queue_full:
                try:
                    self.input_queue.put(rdap_query, block=True, timeout=1)
                    queue_full = False
                except queue.Full:
                    sleep(1)
                    queue_full = True
                    self.logger.info(
                        "Queue Full, Maybe increase number of worker threads!")
                    self.logger.debug(
                        "Queue Full, Trying to put {} in queue again".format(domain))


if __name__ == "__main__":
    pass
