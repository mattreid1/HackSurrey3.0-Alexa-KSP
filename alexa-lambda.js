// This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK (v2).
// Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
// session persistence, api calls, and more.
const Alexa = require('ask-sdk-core');
const WebSocket = require('ws');

const AbortIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AbortIntent';
    },
    handle(handlerInput) {
        const speakOutput = `Aborting now!`;
        const ws = new WebSocket('ws://35.242.157.185');
        ws.on('open', () => {
            ws.send(`abort`);
            ws.close();
        });
        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};

const MunTransferIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'MunTransferIntent';
    },
    handle(handlerInput) {
        const speakOutput = `Setting course for the Mün...`;
        const ws = new WebSocket('ws://35.242.157.185');
        ws.on('open', () => {
            ws.send(`muntransfer`);
            ws.close();
        });
        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};

const CirculariseIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'CirculariseIntent';
    },
    handle(handlerInput) {
        const speakOutput = `Circularising at apoapsis...`;
        const ws = new WebSocket('ws://35.242.157.185');
        ws.on('open', () => {
            ws.send(`circularise`);
            ws.close();
        });
        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};

const SetApoapsisIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'SetApoapsisIntent';
    },
    handle(handlerInput) {
        let altitude = handlerInput.requestEnvelope.request.intent.slots.altitude.value;
        if (altitude === undefined) {
            altitude = "critical error";
        }
        const speakOutput = `Setting the apoapsis to ${altitude} metres.`;
        const ws = new WebSocket('ws://35.242.157.185');
        ws.on('open', () => {
            ws.send(`setapoapsis,${altitude}`);
            ws.close();
        });
        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};

const SetPeriapsisIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'SetPeriapsisIntent';
    },
    handle(handlerInput) {
        let altitude = handlerInput.requestEnvelope.request.intent.slots.altitude.value;
        if (altitude === undefined) {
            altitude = "critical error";
        }
        const speakOutput = `Setting the periapsis to ${altitude} metres.`;
        const ws = new WebSocket('ws://35.242.157.185');
        ws.on('open', () => {
            ws.send(`setperiapsis,${altitude}`);
            ws.close();
        });
        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};

const ExecuteZeroSixNineIntent = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'ExecuteZeroSixNineIntent';
    },
    handle(handlerInput) {
        const speakOutput = `Glory to Arstotzka!`;
        const ws = new WebSocket('ws://35.242.157.185');
        ws.on('open', () => {
            ws.send(`execute069`);
            ws.close();
        });
        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
}

const OrbitIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'OrbitIntent';
    },
    handle(handlerInput) {
        let altitude = handlerInput.requestEnvelope.request.intent.slots.altitude.value;
        if (altitude === undefined) {
            altitude = "critical error";
        }
        const speakOutput = `Setting course for ${altitude} metre orbit Captain.`;
        const ws = new WebSocket('ws://35.242.157.185');
        ws.on('open', () => {
            ws.send(`orbit,${altitude}`);
            ws.close();
        });
        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};

const LaunchRocketIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'LaunchRocketIntent';
    },
    handle(handlerInput) {
        let altitude = handlerInput.requestEnvelope.request.intent.slots.altitude.value;
        if (altitude === undefined) {
            altitude = "critical error";
        }
        const speakOutput = `Engine ignition started! Launching to ${altitude} metres`;
        const ws = new WebSocket('ws://35.242.157.185');
        ws.on('open', () => {
            ws.send(`launch,${altitude}`);
            ws.close();
        });
        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};


const HelpIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.HelpIntent';
    },
    handle(handlerInput) {
        const speakOutput = 'You can say hello to me! How can I help?';

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};
const LaunchRequestHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'LaunchRequest';
    },
    handle(handlerInput) {
        const speakOutput = 'Please make sure you have KSP running before launch.';
        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};
const CancelAndStopIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && (Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.CancelIntent'
                || Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.StopIntent');
    },
    handle(handlerInput) {
        const speakOutput = 'Goodbye!';
        return handlerInput.responseBuilder
            .speak(speakOutput)
            .getResponse();
    }
};
const SessionEndedRequestHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'SessionEndedRequest';
    },
    handle(handlerInput) {
        // Any cleanup logic goes here.
        return handlerInput.responseBuilder.getResponse();
    }
};

// The intent reflector is used for interaction model testing and debugging.
// It will simply repeat the intent the user said. You can create custom handlers
// for your intents by defining them above, then also adding them to the request
// handler chain below.
const IntentReflectorHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest';
    },
    handle(handlerInput) {
        const intentName = Alexa.getIntentName(handlerInput.requestEnvelope);
        const speakOutput = `You just triggered ${intentName}`;

        return handlerInput.responseBuilder
            .speak(speakOutput)
            //.reprompt('add a reprompt if you want to keep the session open for the user to respond')
            .getResponse();
    }
};

// Generic error handling to capture any syntax or routing errors. If you receive an error
// stating the request handler chain is not found, you have not implemented a handler for
// the intent being invoked or included it in the skill builder below.
const ErrorHandler = {
    canHandle() {
        return true;
    },
    handle(handlerInput, error) {
        console.log(`~~~~ Error handled: ${error.stack}`);
        const speakOutput = `Sorry, I had trouble doing what you asked. Please try again.`;

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

// The SkillBuilder acts as the entry point for your skill, routing all request and response
// payloads to the handlers above. Make sure any new handlers or interceptors you've
// defined are included below. The order matters - they're processed top to bottom.
exports.handler = Alexa.SkillBuilders.custom()
    .addRequestHandlers(
        LaunchRequestHandler,
        LaunchRocketIntentHandler,
        OrbitIntentHandler,
        ExecuteZeroSixNineIntent,
        SetPeriapsisIntentHandler,
        SetApoapsisIntentHandler,
        CirculariseIntentHandler,
        MunTransferIntentHandler,
        AbortIntentHandler,
        HelpIntentHandler,
        CancelAndStopIntentHandler,
        SessionEndedRequestHandler,
        IntentReflectorHandler, // make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
    )
    .addErrorHandlers(
        ErrorHandler,
    )
    .lambda();
