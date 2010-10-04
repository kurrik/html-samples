function VideoTile(src, dest, width, height, x, y) {
  this._src = src;
  this._dest = dest;
  this.width = width;
  this.height = height;
  this._hW = width / 2;
  this._hH = height / 2;
  this._srcX = x;
  this._srcY = y;
  this.x = (dest.width / 2) - (src.width / 2) + x + this._hW;
  this.y = dest.height - (src.width / 2) + y + this._hH;
  this.r = 0;
};

VideoTile.prototype.draw = function() {
  var context = this._dest.getContext('2d');
  context.save();
  context.translate(this.x + this._hW, this.y + this._hH);
  context.rotate(this.r);
  context.drawImage(this._src, this._srcX, this._srcY, this.width, 
      this.height, -this._hW, -this._hH, this.width, this.height);
  context.restore();
};

function PhysicsSimulation(width, height) {
  this.ACCURACY = 20;
  
  var padding = 100;
  var aabb = new b2AABB();
  aabb.minVertex.Set(-padding, -padding);
  aabb.maxVertex.Set(width + padding, height + padding);
  
  var gravity = new b2Vec2(0, 100);
  var sleep = false;
  this._world = new b2World(aabb, gravity, sleep);
  console.log(this._world);
  
  this._createBarrier(0, -50, width, 50);                  // Ceiling
  this._createBarrier(0, height + 50, width, 50);          // Ground
  this._createBarrier(-50, height / 2, 50, height);        // Left wall
  this._createBarrier(width + 50, height / 2, 50, height); // Right wall
};

PhysicsSimulation.prototype.setGravity = function(x, y) {
  var gravity = new b2Vec2(x, y);
  this._world.m_gravity = gravity;
};

PhysicsSimulation.prototype._createBarrier = function(x, y, w, h) {
  var shape = new b2BoxDef();
  shape.extents.Set(w, h);
  shape.restitution = 0.0;
  shape.friction = 10;
  
  var body = new b2BodyDef();
  body.AddShape(shape);
  body.position.Set(x, y);
  
  return this._world.CreateBody(body);
};

PhysicsSimulation.prototype.drawWireFrame = function(canvas) {
  var context = canvas.getContext('2d');
  for (var b = this._world.m_bodyList; b; b = b.m_next) {
    for (var s = b.GetShapeList(); s != null; s = s.GetNext()) {
      this._drawShape(s, context);
    }
  }
};

PhysicsSimulation.prototype._drawShape = function(shape, context) {
  context.beginPath();
  switch (shape.m_type) {
    case b2Shape.e_polyShape:
      var poly = shape;
      var tV = b2Math.AddVV(poly.m_position, b2Math.b2MulMV(poly.m_R, poly.m_vertices[0]));
      context.moveTo(tV.x, tV.y);
      for (var i = 0; i < poly.m_vertexCount; i++) {
        var v = b2Math.AddVV(poly.m_position, b2Math.b2MulMV(poly.m_R, poly.m_vertices[i]));
        context.lineTo(v.x, v.y);
      }
      context.lineTo(tV.x, tV.y);
      break;
  }
  context.stroke();
};

PhysicsSimulation.prototype.createBox = function(x, y, w, h) {
  var shape = new b2BoxDef();
  shape.density = 1000;
  shape.friction = 0.1;
  shape.restitution = 0;
  shape.extents.Set(w / 2.0, h / 2.0);
  
  body = new b2BodyDef();
  body.linearVelocity = new b2Vec2(0, 0);
  body.linearDamping = 0;
  body.angularDamping = 0;
  body.AddShape(shape);
  body.position.Set(x, y);
  
  var box = this._world.CreateBody(body);
  return box;
};

PhysicsSimulation.prototype.step = function() {
  var time = new Date().getTime();
  var delta = 0;
  if (this._lastRender == null) {
    this._lastRender = time;
    this._startTime = time;
  } else {
    delta = (time - this._lastRender) / 1000;
    this._lastRender = time;
  }
  this._world.Step(delta, this.ACCURACY);
};

function VideoPhysicsController(parent, width, height) {
  this._proxyTilt = $.proxy(this, '_onTilt'); 
  window.addEventListener('deviceorientation', this._proxyTilt, false);

  this._video = document.createElement('video');
  this._video.addEventListener('canplaythrough', $.proxy(this, '_onVideoLoaded'), false);
  this._video.addEventListener('ended', $.proxy(this, '_onVideoEnded'), false);  
  this._video.loop = true;
  this._video.autoplay = true;
  this._video.src = 'chrome.webm';
  this._video.style.display = 'none';
  parent.appendChild(this._video);
  
  this._buffer = document.createElement('canvas');
  this._output = document.createElement('canvas');
  
  this._output.width = width;
  this._output.height = height;
  parent.appendChild(this._output);
  
  this._physics = new PhysicsSimulation(width, height);
    
  this._tiles = [];
};

VideoPhysicsController.prototype._onVideoEnded = function() {
  console.log('ended');
  this.stop();
};

VideoPhysicsController.prototype._onTilt = function(evt) {
  var x = Math.abs(evt.gamma) > 5 ? 200 * evt.gamma : 0;
  var y = Math.abs(evt.beta) > 10 ? 700 - (200 * -evt.beta) : 700;
  this._physics.setGravity(x, y);
};

VideoPhysicsController.prototype._onVideoLoaded = function() {
  console.log('video loaded');
  this._buffer.width = this._video.videoWidth;
  this._buffer.height = this._video.videoHeight;
  
  var tile_size_x = 64;
  var tile_size_y = 64;
  var tiles_x = Math.floor(this._video.videoWidth / tile_size_x);
  var tiles_y = Math.floor(this._video.videoHeight / tile_size_y);
  
  for (var x = 0; x < tiles_x; x++) {
    for (var y = 0; y < tiles_y; y++) {
      var tile = new VideoTile(this._buffer, this._output, tile_size_x, 
          tile_size_y, x * tile_size_x, y * tile_size_y);
      var mass = this._physics.createBox(tile.x, tile.y, tile.width, 
          tile.height);
      this._tiles.push({tile: tile, mass: mass});
    }
  }
  
  this._video.play();
  
  if (!this._interval) {
    this._interval = window.setInterval($.proxy(this, '_processFrame'), 20);
  }
};

VideoPhysicsController.prototype.stop = function() {
  window.clearInterval(this._interval);  
  this._interval = null;
  this._video.pause();
  window.removeEventListener('deviceorientation', this._proxyTilt, false);
  delete this._video;
  delete this._physics;
};

VideoPhysicsController.prototype._processFrame = function() {
  if (this._video.duration - this._video.currentTime < 0.5) {
    this.stop();
    return;
  }
  var bufferContext = this._buffer.getContext('2d');
  bufferContext.drawImage(this._video, 0, 0);
  var outputContext = this._output.getContext('2d');
  outputContext.clearRect(0, 0, this._output.width, this._output.height);
  this._physics.step();
  
  //this._physics.drawWireFrame(this._output);
  
  for (var i = 0; i < this._tiles.length; i++) {
    var mass = this._tiles[i].mass;
    var tile = this._tiles[i].tile;
    tile.x = mass.m_position0.x - (tile.width / 2);
    tile.y = mass.m_position0.y - (tile.height / 2);
    tile.r = mass.m_rotation;
    tile.draw();
  }
};


function init() {
  var parent = document.body;
  var width = window.innerWidth;
  var height = window.innerHeight;
  var vpc = new VideoPhysicsController(parent, width, height);
};

window.addEventListener('load', init, false);
