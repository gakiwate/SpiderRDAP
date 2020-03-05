import boto3
import logging
from time import sleep


class RDAPInstanceAWS():

    def __init__(self, region, instance_id):
        self.aws_client = boto3.client('ec2', region_name=region)
        self.region = region
        self.instance_id = instance_id
        self.elastic_ip = None
        self.allocation_id = None
        self.association_id = None
        self.logger = logging.getLogger(
            "SpiderRDAPAWS").getChild("RDAPInstanceAWS").getChild(self.instance_id)

        self.logger.info("Start instance if not running")
        self.instance_client = boto3.resource(
            'ec2', region_name=region).Instance(instance_id)
        self.start_instance()

        '''
        First, we see if we have an elastic IP assigned.
        If we do, then we continue otherwise we assign
        an elastic IP.
        '''
        try:
            self.logger.info("Initializing RDAP Instance")
            self.elastic_ip = self.getElasticIP()
            r = self.aws_client.describe_addresses(PublicIps=[self.elastic_ip])
            '''
            Assumption: Only 1 instance? Add explicit check?
            '''
            self.allocation_id = r['Addresses'][0]['AllocationId']
            self.association_id = r['Addresses'][0]['AssociationId']
        except self.aws_client.exceptions.ClientError:
            '''
            Need to assign IPs
            '''
            self.logger.info("AWS Instance has no assigned Elastic IPs.")
            self.assign_new_ips()
        finally:
            '''
            Validate that all values are set
            '''
            ids = [self.elastic_ip, self.allocation_id, self.association_id]
            if any(map(lambda x: x == None, ids)):
                '''
                This should not happen!
                '''
                self.logger.debug("Initialization Failed!")
                self.logger.debug(ids)
                raise Exception

    def start_instance(self):
        self.logger.info("Starting Instance {}")
        self.instance_client.start()
        self.instance_client.wait_until_running()
        self.logger.info("Sleeping for 15 sec")
        sleep(15)

    def stopInstance(self):
        self.release_elastic_ips()
        sleep(5)
        self.instance_client.stop()

    def assign_new_ips(self):
        self.logger.info("Assigning New Elastic IPs")
        attempt = 0
        success = False
        while not success and attempt < 3:
            try:
                r = self.aws_client.allocate_address(Domain='vpc')
                self.allocation_id = r['AllocationId']
                self.elastic_ip = r['PublicIp']
                sleep(1)
                r = self.aws_client.associate_address(
                    AllocationId=self.allocation_id,
                    InstanceId=self.instance_id,
                )
                self.association_id = r['AssociationId']
                success = True
            except Exception as e:
                self.logger.warning(
                    "Assigning new Elastic IPs Failed. Error: {}".format(e))
                sleep(1)
                try:
                    self.logger.warning(
                        "Possible allocation failure. Try and release the address")
                    r = self.aws_client.release_address(
                        AllocationId=self.allocation_id,
                    )
                except Exception as e:
                    self.logger.warning(
                        "Allocation Failure Release also failed. Error: {}".format(e))
                attempt += 1

                if attempt == 3:
                    raise

    def release_elastic_ips(self):
        try:
            r = self.aws_client.disassociate_address(
                AssociationId=self.association_id,
            )
        except Exception as e:
            self.logger.info(
                "Disassociating Address Failed. Error: {}".format(e))
            self.logger.info(
                "Trying to Release Address.")
        try:
            r = self.aws_client.release_address(
                AllocationId=self.allocation_id,
            )
        except Exception as e:
            self.logger.warning(
                "Release Address Failed. Error: {}".format(e))

    def switchElasticIPs(self):
        self.logger.info("Switch Elastic IPs")
        self.release_elastic_ips()
        self.logger.info(
            "Trying to Assign New Address.")

        try:
            self.assign_new_ips()
        except Exception as e:
            self.logger.error(
                "Assigning new IPs Failed. Error: {}".format(e))
            raise

    def getElasticIP(self):
        r = self.aws_client.describe_instances(InstanceIds=[self.instance_id])
        try:
            '''
            Assumption: Only 1 instance? Add explicit check?
            '''
            public_ip = r['Reservations'][0]['Instances'][0]['PublicIpAddress']
        except:
            public_ip = ''
        return public_ip

    def getInfo(self):
        info = {
            'InstanceId': self.instance_id,
            'ElasticIp': self.elastic_ip,
            'AllocationId': self.allocation_id,
            'AssociationId': self.association_id
        }
        return info
