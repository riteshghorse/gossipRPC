from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client


def is_odd(n):
    return n % 2 == 1


server = SimpleXMLRPCServer(("localhost", 8002))
print("Listening on port 8002...")
server.register_function(is_odd, "is_odd")
# server.serve_forever()

with xmlrpc.client.ServerProxy("http://localhost:8001/") as proxy:
    print("3 is even: %s" % str(proxy.is_even(3)))
    print("100 is even: %s" % str(proxy.is_even(100)))


server.serve_forever()
