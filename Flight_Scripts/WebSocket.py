import math
import time
import krpc
import websocket

conn = krpc.connect(name='FlightComputer', address='127.0.0.1', rpc_port=50000, stream_port=50001)
vessel = conn.space_center.active_vessel

start_gravity_turn = 0
end_gravity_turn = 0
ut = None
altitude = None
apoapsis = None
periapsis = None

def prelaunch(sGT=250, eGT=45000):
	global vessel
	global conn
	global ut
	global altitude
	global apoapsis
	global periapsis
	global start_gravity_turn
	global end_gravity_turn

	vessel = conn.space_center.active_vessel
	start_gravity_turn = sGT
	end_gravity_turn = eGT
	ut = conn.add_stream(getattr, conn.space_center, 'ut')
	altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
	apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
	periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
	vessel.control.sas = False
	vessel.control.rcs = True
	vessel.control.throttle = 0

def circularize_burn(): # Circularises at apoapsis
	print('Planning circularization burn')
	mu = vessel.orbit.body.gravitational_parameter
	r = vessel.orbit.apoapsis
	a1 = vessel.orbit.semi_major_axis
	a2 = r
	v1 = math.sqrt(mu * ((2. / r) - (1. / a1)))
	v2 = math.sqrt(mu * ((2. / r) - (1. / a2)))
	delta_v = v2 - v1
	node = vessel.control.add_node(
		ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)

	# Calculate burn time (using rocket equation)
	F = vessel.available_thrust
	Isp = vessel.specific_impulse * 9.82
	m0 = vessel.mass
	m1 = m0 / math.exp(delta_v / Isp)
	flow_rate = F / Isp
	burn_time = (m0 - m1) / flow_rate
	# Orientate ship
	print('Orientating ship for circularization burn')
	vessel.control.rcs = False
	vessel.auto_pilot.reference_frame = node.reference_frame
	vessel.auto_pilot.target_direction = (0, 1, 0)
	vessel.auto_pilot.wait()

	# Wait until burn
	print('Waiting until circularization burn')
	burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time / 2.)
	lead_time = 5
	conn.space_center.warp_to(burn_ut - lead_time)
	# Execute burn
	print('Ready to execute burn')
	time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
	while time_to_apoapsis() - (burn_time / 2.) > 0:
		pass
	print('Executing burn')
	vessel.control.throttle = 1.0
	time.sleep(burn_time - 0.1)
	print('Fine tuning')
	vessel.control.throttle = 0.05
	remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
	while remaining_burn()[1] > 2.0:
		pass
	vessel.control.throttle = 0.0
	node.remove()

	print('Launch complete')

def current_stage():
	return vessel.control.current_stage - 1

def stage_resources():
	return vessel.resources_in_decouple_stage(current_stage()).names

def stage():
	return vessel.control.activate_next_stage()

def liquid_fuel():
	return vessel.resources_in_decouple_stage(current_stage()).amount("LiquidFuel")

def solid_fuel():
	return vessel.resources_in_decouple_stage(current_stage()).amount("SolidFuel")

def liftoff():
	vessel.control.throttle = 1
	stage()
	vessel.auto_pilot.engage()
	vessel.auto_pilot.target_pitch_and_heading(90, 90)

def hohmann_elliptical(r1, r2):
	return math.sqrt(vessel.orbit.body.gravitational_parameter/r1) * (math.sqrt((2*r2)/(r1+r2)) - 1)

def hohmann_circular(r1, r2):
	return math.sqrt(vessel.orbit.body.gravitational_parameter/r2) * (1 - math.sqrt((2*r1)/(r1+r2)))

def set_apoapsis(desired_alt):
	mu = vessel.orbit.body.gravitational_parameter
	delta_v = hohmann_elliptical(vessel.orbit.apoapsis, desired_alt + vessel.orbit.body.equatorial_radius)
	node = vessel.control.add_node(
		ut() + vessel.orbit.time_to_periapsis, prograde=delta_v)
	F = vessel.available_thrust
	Isp = vessel.specific_impulse * 9.82
	m0 = vessel.mass
	m1 = m0 / math.exp(abs(delta_v) / Isp)
	flow_rate = F / Isp
	burn_time = (m0 - m1) / flow_rate

	# Orientate ship
	print('Orientating ship for apoapsis change burn')
	vessel.control.rcs = False
	vessel.control.throttle = 0
	vessel.auto_pilot.engage()
	vessel.auto_pilot.reference_frame = node.reference_frame
	vessel.auto_pilot.wait()

	# Wait until burn
	print('Waiting until apoapsis change burn')
	burn_ut = ut() + vessel.orbit.time_to_periapsis - (burn_time / 2.)
	lead_time = 5
	conn.space_center.warp_to(burn_ut - lead_time)
	# Execute burn
	print('Ready to execute burn')
	time_to_periapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_periapsis')
	while time_to_periapsis() - (burn_time / 2.) > 0:
		pass
	print('Executing burn')
	vessel.control.throttle = 1.0
	time.sleep(burn_time - 0.1)
	print('Fine tuning')
	vessel.control.throttle = 0.05
	remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
	while remaining_burn()[1] > 2.0:
		pass
	vessel.control.throttle = 0.0
	node.remove()

def set_periapsis(desired_alt):
	mu = vessel.orbit.body.gravitational_parameter
	circularize_at_apoapsis = True
	if (desired_alt < apoapsis()):
		circularize_at_apoapsis = False

	delta_v = hohmann_elliptical(vessel.orbit.periapsis, desired_alt + vessel.orbit.body.equatorial_radius)
	node = vessel.control.add_node(
		ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)
	F = vessel.available_thrust
	Isp = vessel.specific_impulse * 9.82
	m0 = vessel.mass
	m1 = m0 / math.exp(abs(delta_v) / Isp)
	flow_rate = F / Isp
	burn_time = (m0 - m1) / flow_rate

	# Orientate ship
	print('Orientating ship for periapsis change burn')
	vessel.control.rcs = False
	vessel.control.throttle = 0
	vessel.auto_pilot.engage()
	vessel.auto_pilot.reference_frame = node.reference_frame
	vessel.auto_pilot.wait()

	# Wait until burn
	print('Waiting until periapsis change burn')
	burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time / 2.)
	lead_time = 5
	conn.space_center.warp_to(burn_ut - lead_time)
	# Execute burn
	print('Ready to execute burn')
	time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
	while time_to_apoapsis() - (burn_time / 2.) > 0:
		pass
	print('Executing burn')
	vessel.control.throttle = 1.0
	time.sleep(burn_time - 0.1)
	print('Fine tuning')
	vessel.control.throttle = 0.05
	remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
	while remaining_burn()[1] > 2.0:
		pass
	vessel.control.throttle = 0.0
	node.remove()

def launch_to(desired_alt):
	liftoff()
	turn_angle = 0
	while True:
		if "LiquidFuel" in stage_resources():
			if (liquid_fuel() == 0):
				stage()
		
		if "SolidFuel" in stage_resources():
			if (solid_fuel() == 0):
				stage()

		if altitude() > start_gravity_turn and altitude() < end_gravity_turn:
			frac = ((altitude() - start_gravity_turn) /
					(end_gravity_turn - start_gravity_turn))
			new_turn_angle = frac * 90
			if abs(new_turn_angle - turn_angle) > 0.5:
				print('Setting angle ' + str(abs(90 - turn_angle)))
				turn_angle = new_turn_angle
				vessel.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)
		if apoapsis() > desired_alt * 0.9:
			print("Target hit")
			break
	
	vessel.control.throttle = 0.25
	while apoapsis() < desired_alt:
		if "LiquidFuel" in stage_resources():
			if (liquid_fuel() == 0):
				stage()
		
		if "SolidFuel" in stage_resources():
			if (solid_fuel() == 0):
				stage()
		pass
	print('Target apoapsis reached')
	vessel.control.throttle = 0.0

	# Wait until out of atmosphere
	print('Coasting out of atmosphere')
	while altitude() < 70500:
		pass
	circularize_burn()

prelaunch()

def on_message(ws, message):
	if (message != "ping"):
		print(message)
	command = message.split(",")[0]
	if (command == "launch"):
		launch_to(int(message.split(",")[1]))
	elif (command == "circularise"):
		circularize_burn()
	elif (command == "setapoapsis"):
		set_apoapsis(int(message.split(",")[1]))
	elif (command == "setperiapsis"):
		set_periapsis(int(message.split(",")[1]))
	elif (command == "execute069"):
		vessel.control.throttle = 1
		vessel.control.rcs = True
		vessel.control.sas = False
		vessel.auto_pilot.engage()
		vessel.auto_pilot.target_pitch_and_heading(90, 270)
		stage()
		time.sleep(1)
		stage()
		vessel.control.throttle = 0
		vessel.auto_pilot.target_pitch_and_heading(0, 270)
		while True:
			if (vessel.flight().pitch <= 40.0):
				break
		vessel.control.throttle = 1

def on_open(ws):
	print("Connected to server!")

def on_close(ws):
	print("Server connection lost!\nReconnecting...")

ws = websocket.WebSocketApp("ws://35.242.157.185/", on_message = on_message, on_close = on_close, on_open = on_open)
ws.run_forever()