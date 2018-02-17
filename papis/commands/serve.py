"""Start a web server listening on port 23119. This server is
compatible with the `zotero connector`. This means that if zotero is
*not* running, you can have items from your web browser added directly
into papis.

This is a rough port of
https://raw.githubusercontent.com/zotero/zotero/master/chrome/content/zotero/xpcom/server_connector.js

"""

import json
import argparse
import logging
import http.server
import papis.config

logger = logging.getLogger("serve")

connector_api_version = 2
zotero_version = "5.0.25"

class Command(papis.commands.Command):

    def init(self):
        self.parser = self.get_subparsers().add_parser(
            "serve",
            help="Start a zotero-connector server"
        )

        self.parser.add_argument(
            "--port",
            help="Port to listen to",
            action="store",
            default=23119
        )

        self.parser.add_argument(
            "--bind",
            help="Address to bind",
            action="store",
            dest="address",
            default="localhost"
        )

        # TODO: no clue on how to do this
        # self.parser.add_argument(
        #     "--fork",
        #     help="Fork the server in background",
        #     action="store_true"
        # )

    def main(self):
        server_address = (self.args.address, self.args.port)
        httpd = http.server.HTTPServer(server_address,
                                       PapisRequestHandler)
        global logger
        logger.info("Starting server")
        httpd.serve_forever()

def papis_add(item):
    # This should just call a papis function that given a dict of
    # properties spit out the correct info.yaml and saves it.
    # I still have to figure out where PDFs are taken
    print(item)
    print("PAPIS add NOT IMPLEMENTED.")

# HTTPRequestHandler class
class PapisRequestHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        global logger
        logger.debug(format % args)
        return

    def set_zotero_headers(self):
        self.send_header("X-Zotero-Version",
                         zotero_version)
        self.send_header("X-Zotero-Connector-API-Version",
                         connector_api_version)
        self.end_headers()

    def read_input(self):
        length = int(self.headers['content-length'])
        return self.rfile.read(length)

    def pong(self, POST = True):
        global logger
        logger.debug("pong")
        # Pong must respond to ping on both GET and POST
        # It must accepts application/json and text/plain
        if not POST: # GET
            logger.debug("GET request")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.set_zotero_headers()
            response = '<!DOCTYPE html><html><head>'+\
                       '<title>Zotero Connector Server is Available</title></head>'+\
	               '<body>Zotero Connector Server is Available</body></html>'
        else: # POST
            logger.debug("POST request")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.set_zotero_headers()

            response = json.dumps({"prefs":{"automaticSnapshots":
                                            papis.config.get('snapshot')}})

        self.wfile.write(bytes(response, "utf8"))

    def papis_collection(self):
        logger.debug("Getting library name")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.set_zotero_headers()
        response = json.dumps(
            {"libraryID":1,
             "libraryName":papis.config.get_lib(),
             "libraryEditable":True, # I'm not aware of a read-only papis mode
             "editable":True,    # collection-level parameters
             "id":None,          # collection-level
             "name": papis.config.get_lib()# collection if collection, else library
            })
        self.wfile.write(bytes(response, "utf8"))

    def add(self):
        # Info or debug?
        logger.info("Adding paper from zotero connector")
        data = json.loads(self.read_input())
        source_uri = data['uri'] # source page
        # debug info
        print(data.keys())
        print(len(data['items']))
        # Add all papers
        for item in data['items']:
            papis_add(item)

        self.send_response(201) # Created
        self.set_zotero_headers()

    def snapshot(self):
        logger.warning("Snapshot not implemented")
        self.send_response(201) # Created
        self.set_zotero_headers()
        return

    def do_POST(self):
        if self.path == "/connector/ping":
            self.pong()
        elif self.path == '/connector/getSelectedCollection':
            self.papis_collection()
        elif self.path == '/connector/saveSnapshot':
            self.snapshot()
        elif self.path == '/connector/saveItems':
            self.add()
        return

    def do_GET(self):
        if self.path == "/connector/ping":
            self.pong(POST = False)
