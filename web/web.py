import os
import tornado.ioloop
import json
import tornado.web
import argparse
import papis.api


"""
tornado
"""

root = os.path.dirname(__file__)


class LibraryHandler(tornado.web.RequestHandler):

    def get(self, arg=""):
        self.set_header('Content-Type', 'application/json')
        # TODO: use to_json() for each p
        data = [{"id": k, "title": p.title, "author": p.author}
                for k, p in enumerate(papis.api.get_documents_in_lib("/tmp/papis"))]
        self.write(json.dumps(data))


class Application(tornado.web.Application):

    def __init__(self, args):
        super(Application, self).__init__(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', "--port", default="8888", type=int)
    parser.add_argument('-a', "--address", default="127.0.0.1", type=str)
    parser.add_argument('-l', "--library", type=str)
    args = parser.parse_args()

    print("start Application ...")
    application = Application([
        (r'/library/(.*)', LibraryHandler),
        (r"/(.*)", tornado.web.StaticFileHandler,
         {"path": root, "default_filename": "template.html"})
    ])

    print("listen on %s:%i ..." % (args.address, args.port))
    application.listen(args.port, address=args.address)
    tornado.ioloop.IOLoop.instance().start()
