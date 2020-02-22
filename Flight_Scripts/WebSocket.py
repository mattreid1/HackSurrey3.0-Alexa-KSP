import krpc
import websocket

def on_message(ws, message):
	print(message)
	global vessel
	for x in range(0, 10):
		print("T-" + str(10 - x))
	vessel.control.throttle = 1
	vessel.control.activate_next_stage()
	vessel.auto_pilot.engage()
	vessel.auto_pilot.target_pitch_and_heading(90, 90)

conn = krpc.connect(name='FlightComputer', address='127.0.0.1', rpc_port=50000, stream_port=50001)
vessel = conn.space_center.active_vessel

ws = websocket.WebSocketApp("ws://35.242.157.185/", on_message = on_message)
ws.run_forever()