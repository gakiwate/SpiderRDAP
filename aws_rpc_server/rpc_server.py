import argparse
import json
import requests
import socket
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def queryRemoteRDAP(query_url):
    try:
        r = requests.get(query_url, timeout=5)
    except Exception as e:
        return 'failed', e
    json_rdap_data = None
    if r.status_code == 200:
        return_code = 'done'
        json_rdap_data = json.loads(r.text)
    else:
        return_code = 'failed'

    return return_code, json_rdap_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='rpcRDAPServer')
    parser.add_argument('--port', action='store', type=int,
                        help='RPC Port', required=True)
    config = parser.parse_args()
    listen_port = config.port

    # get host IP
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)

    # Create server
    with SimpleXMLRPCServer((host_ip, listen_port), requestHandler=RequestHandler) as server:
        server.register_introspection_functions()
        server.register_function(queryRemoteRDAP, 'queryRDAP')
        server.serve_forever()
