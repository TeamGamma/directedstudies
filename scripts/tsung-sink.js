#!/usr/bin/env node

http = require('http');

var total = 0;
var paths = {
};

var port;
if(process.argv.length === 3) {
  port = parseInt(process.argv[2], 10);
} else {
  port = 8000;
}

var server = http.createServer(function(req, res) {
  res.writeHead(200, {});
  res.end('');

  // Update counters
  total += 1;
  if(!paths[req.url]) {
    paths[req.url] = 0;
  }
  paths[req.url] += 1;

});
server.listen(port);
console.log('Listening on port ' + port);

process.on('SIGINT', function() {
  console.log('Received ' + total + ' requests.');
  console.log('Paths: ');
  console.log(paths);

  process.exit();
});

