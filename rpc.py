# done

from xmlrpc import server
import threading
import socketserver
from configuration_manager import ConfigurationManager


class GossipRPCRequestHandler(server.SimpleXMLRPCRequestHandler):
    rpc_paths = ('/', '/RPC2',)


class AsyncXMLRPCServer(socketserver.ThreadingMixIn, server.SimpleXMLRPCServer):
    pass


class XMLRPCGossipManager(object):

    server = None
    server_thread = None

    @staticmethod
    def start_server(gossip_node):

        ip = ConfigurationManager.get_configuration().get_gossip_host()
        port = ConfigurationManager.get_configuration().get_gossip_port()

        print(ip, port)

        if not XMLRPCGossipManager.server and not XMLRPCGossipManager.server_thread:
            XMLRPCGossipManager.server = AsyncXMLRPCServer((ip, port), GossipRPCRequestHandler, allow_none=True,
                                                                logRequests=False)
            XMLRPCGossipManager.server.register_instance(gossip_node)
            XMLRPCGossipManager.server_thread = \
                threading.Thread(target=XMLRPCGossipManager.server.serve_forever)
            XMLRPCGossipManager.server_thread.daemon = True
            XMLRPCGossipManager.server_thread.start()

    @staticmethod
    def stop_server():

        if XMLRPCGossipManager.server and XMLRPCGossipManager.server_thread:
            XMLRPCGossipManager.server.shutdown()
            XMLRPCGossipManager.server.server_close()


class ServerThread(threading.Thread):

    def __init__(self, xml_server):
        threading.Thread.__init__(self)
        self._xml_server = xml_server
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.isSet():
            self._xml_server.handle_request()

    def stop(self):
        self.stop_event.set()


class XMLRPCGossipManagerTest(object):

    server = [None]*5
    server_thread = [None]*5

    @staticmethod
    def start_server(gossip_node, i):

        ip = ConfigurationManager.get_configuration().get_advertised_ip()
        port = ConfigurationManager.get_configuration().get_socket_port()

        if not XMLRPCGossipManagerTest.server[i] and not XMLRPCGossipManagerTest.server_thread[i]:
            XMLRPCGossipManagerTest.server[i] = AsyncXMLRPCServer((ip, port), GossipRPCRequestHandler, allow_none=True,
                                                                logRequests=False)
            XMLRPCGossipManagerTest.server[i].register_instance(gossip_node)
            XMLRPCGossipManagerTest.server_thread[i] = ServerThread(XMLRPCGossipManagerTest.server[i])
                #threading.Thread(target=XMLRPCGossipManagerTest.server[i].serve_forever)
            XMLRPCGossipManagerTest.server_thread[i].daemon = False
            XMLRPCGossipManagerTest.server_thread[i].start()

    @staticmethod
    def stop_server(i):

        if XMLRPCGossipManagerTest.server[i] and XMLRPCGossipManagerTest.server_thread[i]:
            #XMLRPCGossipManagerTest.server[i].shutdown()
            XMLRPCGossipManagerTest.server[i].server_close()
            XMLRPCGossipManagerTest.server[i] = None
            XMLRPCGossipManagerTest.server_thread[i].stop()
            XMLRPCGossipManagerTest.server_thread[i] = None