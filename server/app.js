var net = require('net');

var server = net.createServer(function (s) {
	s.on('data', function(data) {
		try {
			sound = JSON.parse(data);
			console.log('LOGGED ' + sound.user + '/' + sound.level);
			s.write('ACK ' + sound.user + '/' + sound.level + "\n");
		} catch (err) {
			s.write('FCK ' + err + "\n");
		}
	});
});

server.listen(1337);
