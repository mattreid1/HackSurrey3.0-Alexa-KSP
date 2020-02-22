import krpc
import math
import time
import websocket

conn = None
vessel = None
start_gravity_turn = 0
end_gravity_turn = 0
desired_alt = 0
ut = None
altitude = None
apoapsis = None
periapsis = None
stage_2_resources = None
stage_3_resources = None


def prelaunch(sGT=250, eGT=45000, dA=90000):
    global vessel
    global conn
    global ut
    global altitude
    global desired_alt
    global apoapsis
    global periapsis

    global start_gravity_turn
    global end_gravity_turn
    global stage_2_resources
    global stage_3_resources

    conn = krpc.connect(
        name='FlightComputer',
        address='127.0.0.1',
        rpc_port=50000, stream_port=50001)
    vessel = conn.space_center.active_vessel
    start_gravity_turn = sGT
    end_gravity_turn = eGT
    desired_alt = dA
    ut = conn.add_stream(getattr, conn.space_center, 'ut')
    altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
    apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
    periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
    stage_2_resources = vessel.resources_in_decouple_stage(stage=2, cumulative=False)
    stage_3_resources = vessel.resources_in_decouple_stage(stage=3, cumulative=False)
    vessel.control.sas = False
    vessel.control.rcs = False
    vessel.control.throttle = 1.0


def gravity_turn():
    turn_angle = 0
    print(desired_alt)
    while True:
        if altitude() > start_gravity_turn and altitude() < end_gravity_turn:
            frac = ((altitude() - start_gravity_turn) /
                    (end_gravity_turn - start_gravity_turn))
            new_turn_angle = frac * 90
            if abs(new_turn_angle - turn_angle) > 0.5:
                turn_angle = new_turn_angle
                vessel.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)
        if apoapsis() > desired_alt * 0.9:
            print()
            return


def circularize_burn():
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
    while remaining_burn()[1] > 0:
        pass
    vessel.control.throttle = 0.0
    node.remove()

    print('Launch complete')


def launch():
    for x in range(0, 10):
        print("T-" + str(10 - x) + "...")
        time.sleep(1)
    print("Launching")
    vessel.control.activate_next_stage()
    vessel.auto_pilot.engage()
    vessel.auto_pilot.target_pitch_and_heading(90, 90)
    gravity_turn()
    # Disable engines when target apoapsis is reached
    vessel.control.throttle = 0.25
    while apoapsis() < desired_alt:
        pass
    print('Target apoapsis reached')
    vessel.control.throttle = 0.0

    # Wait until out of atmosphere
    print('Coasting out of atmosphere')
    while altitude() < 70500:
        pass
    circularize_burn()


def setAppoapsis(value):
    time_to_periapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_periapsis')
    while time_to_periapsis() > 0:
        pass


switcher = {"launch":launch}


def on_message(ws, message):
    func = switcher.get(message, lambda: "No function")
    func()


def main():
    print("Hello")
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://35.2.42.157.185/", on_message=on_message)
    ws.run_forever()


if __name__ == "__main__":
    main()