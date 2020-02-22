from websocket import create_connection
ws = create_connection("ws://35.242.157.185/")
ws.send("launch,100000")
ws.close()