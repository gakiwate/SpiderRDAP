# SpiderRDAP

RDAP at Scale

This RDAP crawler was designed for research at UCSD.

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
