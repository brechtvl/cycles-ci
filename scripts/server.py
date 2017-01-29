#!/usr/bin/python3

import benchmark
import config
import http.server
import importlib
import os
import socketserver
import threading
import time

# start HTTP server
def run_httpd(httpd):
    httpd.serve_forever()

os.chdir(config.www_dir)
handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(("", 8000), handler)

thread = threading.Thread(target=run_httpd, args=(httpd,))
thread.daemon = True
thread.start()

# system configuration
for command in config.system_config_commands:
    os.system(command)

os.makedirs(config.logs_dir, exist_ok=True)

# detect and execute benchmarks
while 1:
    importlib.reload(benchmark)
    importlib.reload(config)

    benchmark.update_local_tags()

    priority_revisions = []
    revisions = []

    for revision in sorted(os.listdir(config.logs_dir)):
        log_dir = os.path.join(config.logs_dir, revision)
        if os.path.isdir(log_dir):
            if revision.startswith('ci-'):
                priority_revisions += [revision]
            else:
                revisions += [revision]

    for revision in priority_revisions + revisions:
        benchmark.execute(revision)

    time.sleep(10)

