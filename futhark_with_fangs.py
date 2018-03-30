#!/usr/bin/env python3

"""Python module for providing a web RPC frontend to Futhark programs.

Can be run as a program, in which case the first argument must be the
name of a module produced by 'futhark-pyopencl --library' (i.e. the
file name without the 'py' part).
"""

__author__ = "Troels Henriksen"
__copyright__ = "Copyright 2017, Troels Henriksen"
__credits__ = ["Troels Henriksen"]
__license__ = "ISC"
__version__ = "1.0"
__maintainer__ = "Troels Henriksen"
__email__ = "athas@sigkill.dk"
__status__ = "Dangerous"

import io
import pyopencl
from http.server import *

def listify(x):
    """If a tuple, turn into a list.  If not, put it in a single-element list."""
    if type(x) is tuple:
        return list(x)
    else:
        return [x]

class FutharkRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server, module, instance):
        self.instance = instance
        self.module = module
        super().__init__(request, client_address, server)

    def do_POST(self):
        try:
            fname = self.path[1:]
            if not (fname in self.instance.entry_points):
                self.send_error(404, message='valid endpoints are: {}'
                                .format(', '.join(self.instance.entry_points.keys())))
                return

            (param_ts, ret_ts) = self.instance.entry_points[fname]
            reader = self.module.ReaderInput(self.rfile)
            args = list(map(lambda t: self.module.read_value(t, reader=reader), param_ts))

            f = getattr(self.instance, fname)
            try:
                results = listify(f(*args))
            except AssertionError as e:
                self.send_error(400, str(e))
            else:
                self.send_response(200)
                self.end_headers()
                out = io.TextIOWrapper(self.wfile)
                for result in results:
                    # We cannot print PyOpenCL arrays directly, so
                    # turn them into Numpy arrays first.
                    if type(result) == pyopencl.array.Array:
                        result = result.get()
                    self.module.write_value(result, out=out)
                    out.write('\n')
                out.detach() # Avoid closing self.wfile when 'out' goes out of scope.
        except Exception as e:
            self.send_error(500)
            raise e

def futhark_with_fangs(module, instance=None,
                       server_address=('', 8000)):
    """Run a web frontend for a futhark-pyopencl-generated module."""
    if instance == None:
        instance = module.__dict__[module.__name__]()
    httpd = HTTPServer(server_address,
                       lambda request, client_address, server:
                         FutharkRequestHandler(request, client_address, server,
                                               module, instance))
    httpd.serve_forever()

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Futhark with Fangs!')
    parser.add_argument('module', metavar='MODULE',
                        help='The module to serve.')
    parser.add_argument('--host', metavar='HOST', default='',
                        help='The hostname to listen from.')
    parser.add_argument('--port', metavar='PORT', type=int, default=8000,
                        help='The port to listen from.')
    args = parser.parse_args()

    sys.path = ["."] + sys.path
    module = __import__(args.module)
    futhark_with_fangs(module, server_address=(args.host, args.port))
