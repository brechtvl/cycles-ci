#!/usr/bin/python3

import benchmark
import config
import http.server
import importlib
import os
import paths
import socketserver
import threading
import time

# start HTTP server
class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        http.server.SimpleHTTPRequestHandler.end_headers(self)

class TCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_httpd(httpd):
    httpd.serve_forever()

os.chdir(paths.www_dir)
handler = HTTPRequestHandler
httpd = TCPServer(("", 4000), handler)

thread = threading.Thread(target=run_httpd, args=(httpd,))
thread.daemon = True
thread.start()

# system configuration
for command in config.system_config_commands:
    os.system(command)

os.makedirs(paths.logs_dir, exist_ok=True)

# detect and execute benchmarks
while 1:
    importlib.reload(benchmark)
    importlib.reload(config)

    benchmark.update_local_tags()

    ci_ref_revisions = []
    ci_revisions = []
    revisions = []

    for revision in sorted(os.listdir(paths.logs_dir)):
        log_dir = os.path.join(paths.logs_dir, revision)
        if os.path.isdir(log_dir):
            if revision.startswith('ci-'):
                if revision.endswith('-ref'):
                    ci_ref_revisions += [revision]
                else:
                    ci_revisions += [revision]
            else:
                revisions += [revision]

    # benchmark in this order to make equal time comparisons work
    all_revisions = ci_ref_revisions + ci_revisions + revisions
    benchmark.execute(all_revisions)

    time.sleep(10)

