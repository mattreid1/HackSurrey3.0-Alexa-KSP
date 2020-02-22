from websocket import create_connection
ws = create_connection("ws://35.242.157.185/")
ws.send("circularisation,ap")
ws.close()