import boto3
import logging


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

    def assign_new_ips(self):
        self.logger.info("Assigning New Elastic IPs")
        r = self.aws_client.allocate_address(Domain='vpc')
        self.allocation_id = r['AllocationId']
        self.elastic_ip = r['PublicIp']
        r = self.aws_client.associate_address(
            AllocationId=self.allocation_id,
            InstanceId=self.instance_id,
        )
        self.association_id = r['AssociationId']

    def switchElasticIPs(self):
        self.logger.info("Switch Elastic IPs")
        try:
            r = self.aws_client.disassociate_address(
                AssociationId=self.association_id,
            )
            r = self.aws_client.release_address(
                AllocationId=self.allocation_id,
            )
            self.assign_new_ips()
        except Exception as e:
            self.logger.info(
                "Switching Elastic IPs Failed. Error: {}".format(e))
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
