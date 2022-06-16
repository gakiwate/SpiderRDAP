# SpiderRDAP

RDAP at Scale. This RDAP crawler was designed for research at UC San Diego. The name was inspired by a previous crawler which used whois: [SpiderWho](https://github.com/lanrat/SpiderWho).

If you use SpiderRDAP, I would love to hear at gakiwate - at - cs.ucsd.edu.

## Installation

```
git clone https://github.com/gakiwate/SpiderRDAP.git
cd SpiderRDAP
pip3 install .
```

## Code Changes

If you add new features do not forget to upgrade like so.

```
pip3 install . --upgrade
```

## SpiderRDAP

Use SpiderRDAP code for domains that do little to no rate limitting

### Running SpiderRDAP

```
usage: spiderRDAP [-h] --domain-list DOMAIN_LIST --save_path SAVE_PATH
                  [--proxy-list PROXY_LIST] [--workers WORKERS]
                  [--log-level {debug,info,warning,error,critical}] [--quiet]

SpiderRDAP

optional arguments:
  -h, --help            show this help message and exit
  --domain-list DOMAIN_LIST
                        file with list of domains
  --save_path SAVE_PATH
                        file path to save RDAP Output
  --proxy-list PROXY_LIST
                        file with list of proxies to use
  --workers WORKERS     number of workers
  --log-level {debug,info,warning,error,critical}
  --quiet               Quiesce output
```

### Domain List

Newline separated domains in a file

### Proxy List

Newline separated proxies in a file

```
<protocol>://<hostname>:<port>
```

Code tested with socks4.

## SpiderRDAPAWS

Use spiderRDAPAWS for TLDs that do aggressive rate limitting.
You will need to set up AWS instances with tags whose
value matches the ones in aws_config. The AWS Instances
also need to run the rpc server code in aws_rpc_server.

### Running SpiderRDAPAWS

```
usage: spiderRDAPAWS [-h] --domain-list DOMAIN_LIST --save_path SAVE_PATH
                     --aws-config AWS_CONFIG
                     [--log-level {debug,info,warning,error,critical}]
                     [--quiet]

SpiderRDAPAWS

optional arguments:
  -h, --help            show this help message and exit
  --domain-list DOMAIN_LIST
                        file with list of domains
  --save_path SAVE_PATH
                        file path to save RDAP Output
  --aws-config AWS_CONFIG
                        AWS Config File
  --log-level {debug,info,warning,error,critical}
  --batch-multiplier BATCH_MULTIPLIER
                        multiplier to decide on number of domains to batch
  --retry-count RETRY_COUNT
                        number of times to retry RDAP query
  --quiet               Quiesce output
```

### AWS Config Sample

Sample aws_config file

```
{
   "REGIONS": [
      "us-west-1",
   ],
   "TAGS": [
      "rdap"
   ],
   "PORTS": [
      45374
   ]
}
```

Run with spiderRDAPAWSTest to make sure that
the the AWS Credentials and Instances are
up and running

## SpiderRDAPLambda

SpiderRDAPLambda should be used to do bulk queries.

## Running spiderRDAPLambda
```
usage: spiderRDAPLambda [-h] --domain-list DOMAIN_LIST --save-path SAVE_PATH
                        --lambda-workers LAMBDA_WORKERS
                        [--log-level {debug,info,warning,error,critical}]
                        --region
                        {ap-northeast-1,ap-northeast-2,ap-south-1,ap-southeast-1,ap-southeast-2,ca-central-1,eu-central-1,eu-west-1,eu-west-2,eu-west-3,eu-north-1,sa-east-1,us-east-1,us-east-2,us-west-1,us-west-2}
                        [--quiet]

SpiderRDAPLambda

optional arguments:
  -h, --help            show this help message and exit
  --domain-list DOMAIN_LIST
                        file with list of domains
  --save-path SAVE_PATH
                        file path to save RDAP Output
  --lambda-workers LAMBDA_WORKERS
                        number of workers
  --log-level {debug,info,warning,error,critical}
  --region {ap-northeast-1,ap-northeast-2,ap-south-1,ap-southeast-1,ap-southeast-2,ca-central-1,eu-central-1,eu-west-1,eu-west-2,eu-west-3,eu-north-1,sa-east-1,us-east-1,us-east-2,us-west-1,us-west-2}
                        AWS Region to run lambdas from
  --quiet               Quiesce output
```

Note, you can only spawn upto 1000 workers at a time. This is AWS limitation.

If you provide a domain list with more than 1000 domains they will not be queried.
