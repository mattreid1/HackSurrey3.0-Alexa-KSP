const express = require("express");
const Alexa = require("alexa-app");
const PORT = process.env.port || 8080;
const express_app = express();
const app = new Alexa.app("k. s. p.");

app.express({
	expressApp: express_app,
	checkCert: false,
	debug: true
});

app.intent("sayNumber", {
	"slots": { "number": "AMAZON.NUMBER" },
	"utterances": ["say the number {-|number}"]
},
	function (request, response) {
		var number = request.slot("number");
		console.log(`A used said the number ${number}`);
		response.say("You asked for the number " + number);
	}
);

express_app.listen(PORT);
console.log("Listening on port " + PORT);