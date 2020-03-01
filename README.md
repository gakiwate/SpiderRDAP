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

## Running SpiderRDAP
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

## AWS SpiderRDAP

Sample aws_config file
```
{
   "REGIONS": [
      "us-west-1",
   ],
   "TAGS": [
      "rdap"
   ]
}
```

Run with awsTestSpiderRDAP to make sure that
the the AWS Credentials and Instances are
up and running