# Author: Ritesh Ghorse
"""
Basic XML RPC setup
"""

from xmlrpc import server
import threading
import socketserver
from gossip_rpc.config import Configuration
import socket
import os

class GossipRPCRequestHandler(server.SimpleXMLRPCRequestHandler):
    """
    Paths should end in these ways for RPC requests to handle it correctly.
    """
    rpc_paths = ('/', '/RPC2',)


class AsyncXMLRPCServer(socketserver.ThreadingMixIn, server.SimpleXMLRPCServer):
    pass


class XMLRPCGossipManager(object):
    """
    Overrides normal XMLRPC Manger to use threads and
    allowing None values.
    """

    import socket
    server = None
    server_thread = None

    @staticmethod
    def get_ip_port():
        ip = socket.gethostbyname(socket.gethostname())
        configuration = Configuration(os.environ["GOSSIP_CONFIG"])
        port = configuration.get_gossip_port()
        return ip, port

    @staticmethod
    def start_server(gossip_node):
        ip, port = XMLRPCGossipManager.get_ip_port()
        if not XMLRPCGossipManager.server and not XMLRPCGossipManager.server_thread:
            XMLRPCGossipManager.server = AsyncXMLRPCServer((ip, port), GossipRPCRequestHandler, allow_none=True, logRequests=False)
            XMLRPCGossipManager.server.register_instance(gossip_node)
            XMLRPCGossipManager.server_thread = threading.Thread(target=XMLRPCGossipManager.server.serve_forever)
            XMLRPCGossipManager.server_thread.daemon = True
            XMLRPCGossipManager.server_thread.start()

    @staticmethod
    def stop_server():
        if XMLRPCGossipManager.server and XMLRPCGossipManager.server_thread:
            XMLRPCGossipManager.server.shutdown()
            XMLRPCGossipManager.server.server_close()

