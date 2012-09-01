var net = require('net');

var express = require("express");
var app = express()
, http = require('http')
, server = http.createServer(app)
, io = require('socket.io').listen(server);

server.listen(8080);

soundlevel = 0;

app.get('/', function (req, res) {
    res.sendfile(__dirname + '/index.html');
});



io.sockets.on('connection', function (socket) {
    socket.emit('soundlevel', { level: soundlevel });
});


var server = net.createServer(function (s) {
	s.on('data', function(data) {
		try {
			sound = JSON.parse(data);
			console.log('LOGGED ' + sound.user + '/' + sound.level);
            soundlevel = sound.level;
			s.write('ACK ' + sound.user + '/' + sound.level + "\n");
		} catch (err) {
			s.write('FCK ' + err + "\n");
		}
	});
});

server.listen(1337);
