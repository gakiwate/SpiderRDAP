import boto3
import json
import logging
import queue
import threading

from concurrent.futures import ThreadPoolExecutor
from time import sleep

from .rdap_input_aws import RDAPInputAWS
from .rdap_query_worker_aws import RDAPQueryWorkerAWS
from .rdap_save_worker_aws import RDAPSaveWorkerAWS
from .rdap_instance_aws import RDAPInstanceAWS


class RDAPManagerAWS(threading.Thread):
    '''
    Manager thread that is responsible for managing the RDAP crawl.
    '''

    def __init__(self, config):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(
            "SpiderRDAPAWS").getChild("RDAPManagerAWS")
        aws_config = json.load(config.aws_config)
        self.aws_regions = aws_config['REGIONS']
        self.aws_tags = aws_config['TAGS']
        self.aws_ports = aws_config['PORTS']
        self.save_path = config.save_path
        self.retry_count = config.retry_count

        """
        Initialize AWS Instances
        """

        self.aws_instances = []
        for region in self.aws_regions:
            client = boto3.client('ec2', region_name=region)
            r = client.describe_instances(
                Filters=[{'Name': 'tag-key', 'Values': self.aws_tags}])
            for reservation in r.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    self.aws_instances.append(
                        RDAPInstanceAWS(region, instance['InstanceId']))
                    self.logger.info("InstanceId: {}\tPublicDnsName:{}".format(
                        instance['InstanceId'], instance['PublicDnsName']))

        """
        Input Queue is left unbounded because of potential for deadlock
        """
        self.input_queue = queue.Queue()
        self.inputter = RDAPInputAWS(
            self, config.domain_list, config.batch_multiplier, len(self.aws_instances))
        self.save_queue = queue.Queue()

        self.stats = {
            'skipped': 0,
            'failed': 0,
            'in_progress': 0,
            'done': 0,
            'tld_unsupported': 0
        }

        self.logger.info(
            list(map(lambda instance: instance.getElasticIP(), self.aws_instances)))

    def run(self):
        self.logger.info('Starting threads...')
        while not self.save_queue.empty() or not self.input_queue.empty() or not self.inputter.isDone():
            try:
                self.inputter.enqueueDomainBatch()
            except Exception as e:
                self.logger.info("Exception when enqueing {}".format(e))

            self.save_threads = [RDAPSaveWorkerAWS(
                self, self.save_path, self.save_queue) for i in range(0, len(self.aws_instances))]

            self.worker_threads = []
            for elasticIP in map(lambda instance: instance.getElasticIP(), self.aws_instances):
                for port in self.aws_ports:
                    self.worker_threads.append(RDAPQueryWorkerAWS(
                        self, elasticIP, port, self.input_queue, self.save_queue, self.retry_count))

            list(map(lambda thread: thread.start(), self.worker_threads))
            list(map(lambda thread: thread.start(), self.save_threads))

            while self.workerThreadsAlive() or self.saveThreadsAlive():
                self.logger.info(self.stats)
                sleep(5)
                self.logger.debug("Worker Threads Alive: {}".format(
                    self.workerThreadsAlive()))
                self.logger.debug("Save Threads Alive: {}".format(
                    self.saveThreadsAlive()))

            self.logger.info(self.stats)
            with ThreadPoolExecutor(max_workers=len(self.aws_instances)) as executor:
                executor.map(
                    lambda instance: instance.switchElasticIPs(), self.aws_instances)
            self.logger.info(
                list(map(lambda instance: instance.getElasticIP(), self.aws_instances)))

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
