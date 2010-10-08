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

import tornado.httpserver
import tornado.ioloop
import tornado.web
import websocket
import mimetypes
import os
import random
import hashlib
import logging

GRID_DIMENSION = 10

connections = []
board = None
board_items = 0

def reset_board():
  global board
  global board_items
  board = [None] * (GRID_DIMENSION * GRID_DIMENSION)
  board_items = 0
  
def set_move(x, y, c):
  global board
  global board_items
  if board[y * GRID_DIMENSION + x] == None:
    board[y * GRID_DIMENSION + x] = c
    board_items += 1
    if board_items == (GRID_DIMENSION * GRID_DIMENSION):
      reset_board()
      send_all_board()
    return True
  return False

def clean_broken(broken):
  for conn in broken:
    connections.remove(conn)
  
def send_all_board():
  broken_conn = []
  for connection in connections:
    if not connection.send_board():
      broken_conn.append(connection)
  clean_broken(broken_conn)
    
def send_all_move(x, y, c):
  broken_conn = []
  for connection in connections:
    if not connection.send_move(x, y, c):
      broken_conn.append(connection)
  clean_broken(broken_conn)

class WebSocketHandler(websocket.WebSocketHandler):
  def send_board(self):
    global board
    return self.send('BOARD', {'board':board, 'size':GRID_DIMENSION})
  
  def send_move(self, x, y, c):
    return self.send('MOVE', {'x':x, 'y':y, 'c':c})
  
  def open(self):
    print "Open"
    connections.append(self)
    self.send_board()
    self.receive_message(self.on_message)
        
  def send(self, action, data=None):
    payload = { 'action': action }
    if data != None:
      payload['data'] = data
    message = tornado.escape.json_encode(payload)
    try:
      self.write_message(message)
      return True
    except IOError:
      # connection broken
      return False
          
  def on_message(self, message):
    payload = tornado.escape.json_decode(message)
    
    if payload.has_key('action'):
      if payload['action'] == 'MOVE':
        x = payload['data']['x']
        y = payload['data']['y']
        c = payload['data']['c']
        if set_move(x, y, c):
          send_all_move(x, y, c)
    
    self.receive_message(self.on_message)
    
class MainHandler(tornado.web.RequestHandler):
  def get(self):
    client_html_path = os.path.join(os.path.dirname(__file__), "client.html")
    self.render(client_html_path, host=self.request.host)

static_path = os.path.join(os.path.dirname(__file__), "static")
application = tornado.web.Application([
    (r"/websocket", WebSocketHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, { "path": static_path }),
    (r"/", MainHandler),
], **{
    "debug": True,
})

if __name__ == "__main__":
  reset_board()
  
  port = 80 
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(port)
  print "Started server on port %s" % port
  tornado.ioloop.IOLoop.instance().start()
