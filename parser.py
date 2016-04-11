import subprocess
import ssl
import socket
import socketserver
import jsonpickle
from es_result import es_result

class parser(socketserver.BaseRequestHandler):
    cert_file="<insert pub cert file>"
    key_file="<insert priv cert file>"

    def __init__(self,search):
        self.search = search
        es_result.init()

    def setup(self):
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)

    def handle(self):
        print("New connection from " + str(self.client_address))
        connstream = self.context.wrap_socket(self.request, server_side=True)
        print("Connection unwraped from " + str(connstream.getpeername()))
        try:
            data = connstream.recv()
            concat=data.decode('utf-8')
            while self.parse_beacon(connstream, self.decode(concat)):
                data = connstream.recv()
                concat+=data.decode('utf-8')
        finally:
            connstream.shutdown(socket.SHUT_RDWR)
            connstream.close()

    def decode(self,data):
        try:
            resp=jsonpickle.decode(data)
            print("Response decoded to: " + type(resp).__name__, end="")
            return resp
        except:
            print("Failed to decode... probably still receiving. Data:\n" + str(data))
            return None

    def parse_result(self, connstream, r):
        if r != None and type(r).__name__ == "Result":
            if r.data:
                print("Source:\n" + r.source + "\nData:\n" + str(r.data))
                searchhits, regexhits = search.apply_terms(r.data)
                print("Searchhits: " + str(searchhits))
                print("Regexhits: " + str(regexhits))
                esr = es_result()
                esr.source = r.source
                esr.referrer = r.referrer
                esr.data = r.data
                esr.dataHash = r.dataHash
                if len(regexhits) > 0:
                    esr.regex_hit = 1
                    esr.regex_hits = "\n".join(regex_hits)
                else:
                    esr.regex_hit = 0
                if len(searchhits) > 0:
                    esr.searchterm_hit = 1
                    esr.searchterm_hits = "\n".join(searchhits)
                else:
                    esr.searchterm_hit = 0
                esr.timeStart = r.timeStart
                esr.timeEnd = r.timeEnd
                c = r.crawlerConfig
                esr.config_name = c.name
                esr.config_location = c.location
                esr.config_protocol = c.protocol
                esr.config_speed = c.speed
                esr.config_depth = c.depth
                esr.config_maxDepth = c.maxDepth
                esr.config_options = c.options
                esr.save()
            return True
        return False

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 4443
    parser = socketserver.TCPServer((HOST, PORT), parser)
    parser.serve_forever()