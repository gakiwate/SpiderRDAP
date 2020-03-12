import boto3
import json
import logging
import queue
import threading
import time
import random


class RDAPQueryWorkerLambda(threading.Thread):

    def __init__(self, manager, region, input_queue, save_queue):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(
            "SpiderRDAPLambda").getChild("RDAPQueryWorkerLambda")
        self.manager = manager
        self.aws_client = boto3.client('lambda', region_name=region)
        self.input_queue = input_queue
        self.save_queue = save_queue

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
                continue

            self.manager.incrInProgress()
            domain = rdap_work_info["domain"]
            return_code, ip, json_rdap_data = self.rdap_query(rdap_work_info)
            self.logger.info("Lambda IP: {}".format(ip))
            self.manager.lambda_ips.append(ip)
            self.manager.decrInProgress()

            timestamp = time.time()
            if return_code == 'done':
                self.manager.incrDone()
                self.save_queue.put(
                    {'error': None, 'data': json_rdap_data, 'domain': domain, 'timestamp': timestamp})
            elif return_code == 'failed':
                self.manager.incrFailed()
                self.save_queue.put(
                    {'error': 'failed', 'data': rdap_work_info, 'domain': domain, 'timestamp': timestamp})
                self.logger.info(
                    "Failed: {}".format(rdap_work_info))
            else:  # return_code == 'tld_rdap_unsupported'
                self.manager.incrTLDUnsupported()
                self.manager.incrSkipped()
                self.save_queue.put(
                    {'error': 'tld_unsupported', 'data': rdap_work_info, 'domain': domain, 'timestamp': timestamp})

            self.logger.debug("Marking task done!")
            self.input_queue.task_done()

    def rdap_query(self, rdap_work_info):
        domain = rdap_work_info["domain"]
        if len(rdap_work_info["rdap_url"]) == 0:
            return 'tld_rdap_unsupported', '', None
        rdap_url = rdap_work_info["rdap_url"][rdap_work_info['attempt'] % len(
            rdap_work_info["rdap_url"])]
        query_url = "{}/domain/{}".format(rdap_url, domain)
        query_payload = json.dumps({"query_url": query_url})
        self.logger.debug(
            "Starting Lambda with Payload: {}".format(query_payload))

        json_rdap_data = None
        try:
            time.sleep(random.uniform(0, 3))
            response = self.aws_client.invoke(
                FunctionName='rdap-lambda',
                InvocationType='RequestResponse',
                Payload=query_payload)

            if response['StatusCode'] == 200:
                return_code, ip, json_rdap_data = json.loads(
                    response['Payload'].read())
            else:  # Error
                error = response['Payload'].read().decode('utf-8')
                self.logger.info("Lambda Request Failed: {}".format(error))
                return 'failed', '', error
        except Exception as e:
            self.logger.info("Lambda Request Failed: {}".format(e))
            return 'failed', '', e

        return return_code, ip, json_rdap_data


if __name__ == "__main__":
    pass
