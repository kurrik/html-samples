import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import mimetypes
import os
import random
import hashlib
import threading
import time

NUM_TILES = 10

connections = []

FRAME_TILES = None
FRAME_INDEX = 0
TILE_QUEUE = []
FRAME_LAST_TIME = 0
FRAME_FPS = 0

def init_frame():
  global FRAME_INDEX
  global FRAME_TILES
  global NUM_TILES
  global TILE_QUEUE
  global FRAME_LAST_TIME
  
  TILE_QUEUE = []
  FRAME_INDEX = FRAME_INDEX + 1
  FRAME_TILES = [None] * NUM_TILES
  FRAME_LAST_TIME = time.time()
  
  for i in range(NUM_TILES):
    FRAME_TILES[i] = [None] * NUM_TILES

def tile_queue_next():
  global TILE_QUEUE
  global NUM_TILES
  if len(TILE_QUEUE) == 0:
    for x in range(NUM_TILES):
      for y in range(NUM_TILES):
        if FRAME_TILES[x][y] == None:
          TILE_QUEUE.append((x, y))
  if len(TILE_QUEUE) > 0:
    return TILE_QUEUE.pop(0)
  else:
    return None

def next_tile():
  global FRAME_INDEX
  global FRAME_TILES
  global NUM_TILES
  global FRAME_FPS
  
  if FRAME_TILES == None:
    init_frame()
  
  tile = tile_queue_next()
  if tile != None:
    return {
      'x': tile[0], 
      'y': tile[1], 
      'frame': FRAME_INDEX, 
      'tiles': NUM_TILES,
      'connections': len(connections),
      'fps': FRAME_FPS,
    }
  
  elapsed = time.time() - FRAME_LAST_TIME
  FRAME_FPS = 1 / elapsed
  
  send_frame()
  init_frame()
  return {
    'x': 0,
    'y': 0,
    'frame': FRAME_INDEX,
    'tiles': NUM_TILES,
    'connections': len(connections),
    'fps': FRAME_FPS,
  }

def set_tile(i, j, index, tile):
  global FRAME_INDEX
  global FRAME_TILES
  if index == FRAME_INDEX and FRAME_TILES[i][j] is None:
    FRAME_TILES[i][j] = tile

def send_frame():
  global FRAME_INDEX
  global FRAME_TILES
  global FRAME_LAST_TIME
  
  for connection in connections:
    connection.send('FRAME', {
      'frame': FRAME_INDEX,
      'imagedata': FRAME_TILES,
      'tiles': NUM_TILES,
    })

class WebSocketHandler(tornado.websocket.WebSocketHandler):
  def __init__(self, *args, **kwargs):
    super(WebSocketHandler, self).__init__(*args, **kwargs)
    
  def __del__(self):
    super(WebSocketHandler, self).__del__()
    
  def open(self):
    print "Open"
    connections.append(self)
    self.receive_message(self.on_message)
        
  def send(self, action, data=None):
    payload = { 'action': action }
    if data != None:
      payload['data'] = data
    message = tornado.escape.json_encode(payload)
    try:
      self.write_message(message)
    except IOError:
      # connection broken
      connections.remove(self)
          
  def on_message(self, message):
    print "Message: %s" % message
    payload = tornado.escape.json_decode(message)
    
    if payload.has_key('action'):
      if payload['action'] == 'NEEDTILE':
        self.send('TILE', next_tile())
      elif payload['action'] == 'TILE':
        set_tile(payload['data']['x'], payload['data']['y'], 
            payload['data']['frame'], payload['data']['data'])
    
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
    port = 80 
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    print "Started server on port %s" % port
    tornado.ioloop.IOLoop.instance().start()
