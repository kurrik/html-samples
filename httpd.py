#!/usr/bin/python
# Copyright 2010 Google, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import BaseHTTPServer
import logging
import os
import SimpleHTTPServer
import SocketServer
import sys

logging.getLogger().setLevel(logging.INFO)

SERVER_PORT = 5200
SERVER_HOST = 'localhost'
SAFE_DIR_COMPONENTS = ['html-samples']
SAFE_DIR_SUFFIX = apply(os.path.join, SAFE_DIR_COMPONENTS)

def check():
  if os.getcwd().endswith(SAFE_DIR_SUFFIX):
    return
  logging.error('httpd.py should only be run from the %s', SAFE_DIR_SUFFIX)
  logging.error('directory for testing purposes.')
  logging.error('We are currently in %s', os.getcwd())
  sys.exit(1)

class AlmostSimpleHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_GET(self):
    if self.path == '/':
      self.send_response(301)
      self.send_header('Location', '/index.html')
      self.end_headers()
      return

    # old style approach instead of super()
    return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

class ThreadedServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
  pass

def run(server_address,
        server_class=ThreadedServer,
        handler_class=AlmostSimpleHTTPRequestHandler):
  httpd = server_class(server_address, handler_class)
  logging.info('started server on port %d', httpd.server_address[1])
  httpd.serve_forever()

if __name__ == '__main__':
  check()
  if len(sys.argv) > 1:
    run((SERVER_HOST, int(sys.argv[1])))
  else:
    run((SERVER_HOST, SERVER_PORT))
