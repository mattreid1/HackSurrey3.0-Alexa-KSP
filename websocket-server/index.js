const WebSocket = require("ws");

const wss = new WebSocket.Server({ port: 80 });

wss.on("connection", function connection(connection) {
	console.log("Client connected!");

	connection.on("message", function incoming(data) {
		console.log(data);
		wss.clients.forEach(function each(client) {
			if (client !== connection && client.readyState === WebSocket.OPEN) {
				client.send(data);
			}
		});
	});
});