# done

from xmlrpc import server
import threading
import socketserver
from configuration_manager import ConfigurationManager


class ChordRPCRequestHandler(server.SimpleXMLRPCRequestHandler):
    rpc_paths = ('/', '/RPC2',)


class AsyncXMLRPCServer(socketserver.ThreadingMixIn, server.SimpleXMLRPCServer):
    pass


class XMLRPCChordServerManager(object):

    server = None
    server_thread = None

    @staticmethod
    def start_server(chord_node):

        ip = ConfigurationManager.get_configuration().get_gossip_host()
        port = ConfigurationManager.get_configuration().get_gossip_port()

        print(ip, port)

        if not XMLRPCChordServerManager.server and not XMLRPCChordServerManager.server_thread:
            XMLRPCChordServerManager.server = AsyncXMLRPCServer((ip, port), ChordRPCRequestHandler, allow_none=True,
                                                                logRequests=False)
            XMLRPCChordServerManager.server.register_instance(chord_node)
            XMLRPCChordServerManager.server_thread = \
                threading.Thread(target=XMLRPCChordServerManager.server.serve_forever)
            XMLRPCChordServerManager.server_thread.daemon = True
            XMLRPCChordServerManager.server_thread.start()

    @staticmethod
    def stop_server():

        if XMLRPCChordServerManager.server and XMLRPCChordServerManager.server_thread:
            XMLRPCChordServerManager.server.shutdown()
            XMLRPCChordServerManager.server.server_close()


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


class XMLRPCChordServerManagerTest(object):

    server = [None]*5
    server_thread = [None]*5

    @staticmethod
    def start_server(chord_node, i):

        ip = ConfigurationManager.get_configuration().get_advertised_ip()
        port = ConfigurationManager.get_configuration().get_socket_port()

        if not XMLRPCChordServerManagerTest.server[i] and not XMLRPCChordServerManagerTest.server_thread[i]:
            XMLRPCChordServerManagerTest.server[i] = AsyncXMLRPCServer((ip, port), ChordRPCRequestHandler, allow_none=True,
                                                                logRequests=False)
            XMLRPCChordServerManagerTest.server[i].register_instance(chord_node)
            XMLRPCChordServerManagerTest.server_thread[i] = ServerThread(XMLRPCChordServerManagerTest.server[i])
                #threading.Thread(target=XMLRPCChordServerManagerTest.server[i].serve_forever)
            XMLRPCChordServerManagerTest.server_thread[i].daemon = False
            XMLRPCChordServerManagerTest.server_thread[i].start()

    @staticmethod
    def stop_server(i):

        if XMLRPCChordServerManagerTest.server[i] and XMLRPCChordServerManagerTest.server_thread[i]:
            #XMLRPCChordServerManagerTest.server[i].shutdown()
            XMLRPCChordServerManagerTest.server[i].server_close()
            XMLRPCChordServerManagerTest.server[i] = None
            XMLRPCChordServerManagerTest.server_thread[i].stop()
            XMLRPCChordServerManagerTest.server_thread[i] = None