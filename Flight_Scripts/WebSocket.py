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

def circularize_burn(rcs = False): # Circularises at apoapsis
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
	Isp = vessel.specific_impulse * vessel.orbit.body.surface_gravity
	m0 = vessel.mass
	m1 = m0 / math.exp(delta_v / Isp)
	flow_rate = F / Isp
	burn_time = abs((m0 - m1) / flow_rate)
	# Orientate ship
	print('Orientating ship for circularization burn')
	vessel.control.rcs = rcs
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
	end_time = ut() + burn_time
	while (end_time - 1) > ut():
		checkFuel()
	print('Fine tuning')
	vessel.control.throttle = 0.05
	remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
	while remaining_burn()[1] > 2.0: # 2m/s
		checkFuel()
	vessel.control.throttle = 0.0
	node.remove()

def circularize_burn_periapsis(rcs = False):
	print('Planning circularization burn')
	mu = vessel.orbit.body.gravitational_parameter
	r = vessel.orbit.periapsis
	a1 = vessel.orbit.semi_major_axis
	a2 = r
	v1 = math.sqrt(mu * ((2. / r) - (1. / a1)))
	v2 = math.sqrt(mu * ((2. / r) - (1. / a2)))
	delta_v = v2 - v1
	node = vessel.control.add_node(
		ut() + vessel.orbit.time_to_periapsis, prograde=delta_v)

	# Calculate burn time (using rocket equation)
	F = vessel.available_thrust
	Isp = vessel.specific_impulse * vessel.orbit.body.surface_gravity
	m0 = vessel.mass
	m1 = m0 / math.exp(delta_v / Isp)
	flow_rate = F / Isp
	burn_time = abs((m0 - m1) / flow_rate)
	# Orientate ship
	print('Orientating ship for circularization burn')
	vessel.control.rcs = rcs
	vessel.auto_pilot.reference_frame = node.reference_frame
	vessel.auto_pilot.target_direction = (0, 1, 0)
	vessel.auto_pilot.wait()

	# Wait until burn
	print('Waiting until circularization burn')
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
	end_time = ut() + burn_time
	while (end_time - 1) > ut():
		checkFuel()
	print('Fine tuning')
	vessel.control.throttle = 0.05
	remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
	while remaining_burn()[1] > 2.0:
		checkFuel()
	vessel.control.throttle = 0.0
	node.remove()

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

def checkFuel():
	if "LiquidFuel" in stage_resources():
		if (liquid_fuel() <= 0.1):
			stage()
	
	if "SolidFuel" in stage_resources():
		if (solid_fuel() <= 0.1):
			stage()

def set_apoapsis(desired_alt, rcs=False):
	mu = vessel.orbit.body.gravitational_parameter
	delta_v = hohmann_elliptical(vessel.orbit.apoapsis, desired_alt + vessel.orbit.body.equatorial_radius)
	node_time = ut() + vessel.orbit.time_to_periapsis
	node = vessel.control.add_node(node_time, prograde=delta_v)
	F = vessel.available_thrust
	Isp = vessel.specific_impulse * vessel.orbit.body.surface_gravity
	m0 = vessel.mass
	m1 = m0 / math.exp(abs(delta_v) / Isp)
	flow_rate = F / Isp
	burn_time = abs((m0 - m1) / flow_rate)

	# Orientate ship
	print('Orientating ship for apoapsis change burn')
	vessel.control.rcs = rcs
	vessel.control.throttle = 0
	vessel.auto_pilot.engage()
	vessel.auto_pilot.reference_frame = node.reference_frame
	vessel.auto_pilot.wait()

	# Wait until burn
	print('Waiting until apoapsis change burn')
	burn_ut = node_time - (burn_time / 2.)
	lead_time = 5
	conn.space_center.warp_to(burn_ut - lead_time)
	# Execute burn
	print('Ready to execute burn')
	while ut() - (node_time + (burn_time / 2.)) > 0:
		pass
	print('Executing burn')
	vessel.control.throttle = 1.0
	end_time = ut() + burn_time
	while (end_time - 1) > ut():
		checkFuel()
	print('Fine tuning')
	vessel.control.throttle = 0.05
	remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
	while remaining_burn()[1] > 2.0:
		pass
	vessel.control.throttle = 0.0
	node.remove()

def set_periapsis(desired_alt, rcs=False):
	mu = vessel.orbit.body.gravitational_parameter
	delta_v = hohmann_elliptical(vessel.orbit.periapsis, desired_alt + vessel.orbit.body.equatorial_radius)
	node_time = ut() + vessel.orbit.time_to_apoapsis
	node = vessel.control.add_node(node_time, prograde=delta_v)
	F = vessel.available_thrust
	Isp = vessel.specific_impulse * vessel.orbit.body.surface_gravity
	m0 = vessel.mass
	m1 = m0 / math.exp(abs(delta_v) / Isp)
	flow_rate = F / Isp
	burn_time = abs((m0 - m1) / flow_rate)

	# Orientate ship
	print('Orientating ship for periapsis change burn')
	vessel.control.rcs = rcs
	vessel.control.throttle = 0
	vessel.auto_pilot.engage()
	vessel.auto_pilot.reference_frame = node.reference_frame
	vessel.auto_pilot.wait()

	# Wait until burn
	print('Waiting until periapsis change burn')
	burn_ut = node_time - (burn_time / 2.)
	lead_time = 5
	conn.space_center.warp_to(burn_ut - lead_time)
	# Execute burn
	print('Ready to execute burn')
	time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
	while ut() - (node_time + (burn_time / 2.)) > 0:
		pass
	print('Executing burn')
	vessel.control.throttle = 1.0
	end_time = ut() + burn_time
	while (end_time - 1) > ut():
		checkFuel()
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
		checkFuel()
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
		checkFuel()

	print('Target apoapsis reached')
	vessel.control.throttle = 0.0

	# Wait until out of atmosphere
	print('Coasting out of atmosphere')
	while altitude() < 70500:
		pass
	circularize_burn()
	print("Launch complete!")

def mun_transfer():
	print("Starting transfer")
	vessel.control.toggle_action_group(1)
	celestial_body = conn.space_center.bodies["Mun"]
	destSemiMajor = celestial_body.orbit.semi_major_axis
	hohmannSemiMajor = destSemiMajor / 2
	neededPhase = 2 * math.pi * (1 / (2 * (destSemiMajor ** 3 / hohmannSemiMajor ** 3) ** (1 / 2)))
	optimalPhaseAngle = 180 - neededPhase * 180 / math.pi  # In degrees; for mun, mun should be ahead of vessel

	# Get current phase angle
	phaseAngle = 5040  # Random default value
	vessel.control.rcs = True
	vessel.auto_pilot.engage()
	vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
	vessel.auto_pilot.target_direction = (0.0, 1.0, 0.0)  # Point pro-grade
	vessel.auto_pilot.wait()

	angleDec = False  # Whether or not phase angle is decreasing; used to make sure mun is ahead of vessel
	prevPhase = 0
	while abs(phaseAngle - optimalPhaseAngle) > 1 or not angleDec:
		bodyRadius = celestial_body.orbit.radius
		vesselRadius = vessel.orbit.radius

		time.sleep(1)

		bodyPos = celestial_body.orbit.position_at(conn.space_center.ut,
												   celestial_body.reference_frame)
		vesselPos = vessel.orbit.position_at(conn.space_center.ut, celestial_body.reference_frame)

		bodyVesselDistance = ((bodyPos[0] - vesselPos[0]) ** 2 + (bodyPos[1] - vesselPos[1]) ** 2 + (
				bodyPos[2] - vesselPos[2]) ** 2) ** (1 / 2)

		try:
			phaseAngle = math.acos(
				(bodyRadius ** 2 + vesselRadius ** 2 - bodyVesselDistance ** 2) / (2 * bodyRadius * vesselRadius))
		except:
			print("Domain error! Cannot calculate. Standby...")
			continue  # Domain error
		phaseAngle = phaseAngle * 180 / math.pi

		if prevPhase - phaseAngle > 0:
			angleDec = True
			if abs(phaseAngle - optimalPhaseAngle) > 18:
				conn.space_center.rails_warp_factor = 4
			else:
				conn.space_center.rails_warp_factor = 0
		else:
			angleDec = False
			conn.space_center.rails_warp_factor = 4

		prevPhase = phaseAngle

		print("Phase:", phaseAngle)

	# Use vis-viva to calculate deltaV required to raise orbit to that of the moon
	mu = vessel.orbit.body.gravitational_parameter  # Get gravitation parameter (mu) for Kerbin
	r = vessel.orbit.radius
	a = vessel.orbit.semi_major_axis

	v1 = math.sqrt(mu * ((2 / r) - (1 / a)))

	a = (celestial_body.orbit.radius + vessel.orbit.radius) / 2

	v2 = math.sqrt(mu * ((2 / r) - (1 / a)))

	delta_v = v2 - v1
	print("Maneuver Now With DeltaV:", delta_v)

	actual_delta_v = 0
	vessel.control.throttle = 1.0
	while (delta_v > actual_delta_v):
		time.sleep(0.15)
		r = vessel.orbit.radius
		a = vessel.orbit.semi_major_axis
		actual_delta_v = (mu * ((2 / r) - (1 / a))) ** (1 / 2) - v1
		print("DeltaV so far: ", actual_delta_v, "out of needed", delta_v)
		checkFuel()
	vessel.control.throttle = 0
	vessel.auto_pilot.disengage()
	print("Burn complete")
	cir_moon()


def cir_moon():
	conn.space_center.warp_to(ut() + vessel.orbit.time_to_soi_change + vessel.orbit.next_orbit.time_to_periapsis - 120)
	print('Planning Munar circularisation burn')
	mu = vessel.orbit.body.gravitational_parameter
	r = vessel.orbit.periapsis
	a1 = vessel.orbit.semi_major_axis
	a2 = r
	v1 = math.sqrt(mu * ((2. / r) - (1. / a1)))
	v2 = math.sqrt(mu * ((2. / r) - (1. / a2)))
	delta_v = v2 - v1
	nodeTime = ut() + vessel.orbit.time_to_periapsis
	node = vessel.control.add_node(nodeTime, prograde=delta_v)

	# Calculate burn time (using rocket equation)
	F = vessel.available_thrust
	Isp = vessel.specific_impulse * vessel.orbit.body.surface_gravity
	m0 = vessel.mass
	m1 = m0 / math.exp(delta_v / Isp)
	flow_rate = F / Isp
	burn_time = abs((m0 - m1) / flow_rate)
	# Orientate ship
	print('Orientating ship for Munar capture burn')
	vessel.control.rcs = True
	vessel.auto_pilot.engage()
	vessel.auto_pilot.reference_frame = node.reference_frame
	vessel.auto_pilot.target_direction = (0, 1, 0)
	vessel.auto_pilot.wait()

	# Wait until burn
	print('Waiting until Munar capture burn')
	burn_ut = nodeTime - (burn_time / 2.)
	lead_time = 5
	conn.space_center.warp_to(burn_ut - lead_time)
	# Execute burn
	print('Ready to execute burn')
	time_to_periapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_periapsis')
	while time_to_periapsis() - (burn_time / 2.) > 0:
		pass
	print('Executing burn')
	vessel.control.throttle = 1.0
	end_time = ut() + burn_time
	while (end_time - 10) > ut():
		checkFuel()
	print('Fine tuning')
	vessel.control.throttle = 0.1
	remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
	while remaining_burn()[1] > 10.0:
		checkFuel()
	vessel.control.throttle = 0.0
	node.remove()
	lower_mun_orbit()

def lower_mun_orbit():
	print("Lowering to 30,000 metres")
	vessel.control.rcs = True
	vessel.auto_pilot.engage()
	set_periapsis(30000, True)
	circularize_burn_periapsis(True)
	print("Welcome to the Mün!")

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
	elif (command == "muntransfer"):
		mun_transfer()
	elif (command == "abort"):
		vessel.control.abort = True
	elif (command == "execute069"):
		vessel.control.throttle = 0.3
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
			if (vessel.flight().pitch <= 5.0):
				break
		vessel.control.throttle = 1
		time.sleep(3.2)
		vessel.control.toggle_action_group(1)

def on_open(ws):
	print("Connected to server!")

def on_close(ws):
	print("Server connection lost!\nReconnecting...")

mun_transfer()
ws = websocket.WebSocketApp("ws://35.242.157.185/", on_message = on_message, on_close = on_close, on_open = on_open)
ws.run_forever()