import json
import logging
import queue
import requests

from collections import defaultdict


class RDAPInputAWS():
    '''
    RDAPInput
    '''

    def __init__(self, manager, domain_list, num_instances):
        self.logger = logging.getLogger(
            "SpiderRDAPAWS").getChild("RDAPInputAWS")
        self.manager = manager
        self.domain_list = list(domain_list.read().splitlines())
        self.all_done = False
        """
        for every batch we get 15 domains per instance
        """
        self.batch_size = 15 * num_instances
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

    def isDone(self):
        return self.all_done

    def enqueueDomainBatch(self):
        '''
        The RDAPInputAWS needs to batch the
        domains since the consumption model
        is different. After, the batch size
        number of domains are consumed we
        change IPs and then start again.
        '''
        if len(self.domain_list) == 0:
            self.all_done = True
        domain_batch = []
        while len(domain_batch) < self.batch_size:
            try:
                domain = self.domain_list.pop()
                domain = domain.strip()
                domain_batch.append(domain)
            except IndexError:
                break

        self.enqueue_batch(domain_batch)

    def enqueue_batch(self, domain_batch):
        for domain in domain_batch:
            rdap_query = self.construct_query(domain)
            self.input_queue.put(rdap_query, block=True, timeout=5)
            self.logger.debug("Input Queue Size: {}".format(
                self.input_queue.qsize()))


if __name__ == "__main__":
    pass
