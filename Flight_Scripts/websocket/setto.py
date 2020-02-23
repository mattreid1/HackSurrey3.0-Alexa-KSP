from websocket import create_connection
ws = create_connection("ws://35.242.157.185/")
ws.send("setapoapsis,200000")
ws.close()