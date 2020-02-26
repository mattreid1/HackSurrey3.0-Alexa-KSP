import math
import time
import krpc

conn = krpc.connect(name="FlightComputer", address="127.0.0.1", rpc_port=50000, stream_port=50001)
vessel = conn.space_center.active_vessel

start_gravity_turn = 250
end_gravity_turn = 50000
ut = conn.add_stream(getattr, conn.space_center, "ut")
altitude = conn.add_stream(getattr, vessel.flight(), "mean_altitude")
apoapsis = conn.add_stream(getattr, vessel.orbit, "apoapsis_altitude")
periapsis = conn.add_stream(getattr, vessel.orbit, "periapsis_altitude")
vessel.auto_pilot.engage()
auto_pilot = vessel.auto_pilot


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


def hohmann_elliptical(r1, r2):
    return math.sqrt(vessel.orbit.body.gravitational_parameter / r1) * (math.sqrt((2 * r2) / (r1 + r2)) - 1)


def hohmann_circular(r1, r2):
    return math.sqrt(vessel.orbit.body.gravitational_parameter / r2) * (1 - math.sqrt((2 * r1) / (r1 + r2)))


def checkFuel():
    if "LiquidFuel" in stage_resources():
        if (liquid_fuel() <= 0.1):
            stage()

    if "SolidFuel" in stage_resources():
        if (solid_fuel() <= 0.1):
            stage()


def circularise(at_apoapsis=True, rcs=False):  # Circularises (default at periapsis, no RCS)
    print("Planning circularization burn...")
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis if at_apoapsis else vessel.orbit.periapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu * ((2. / r) - (1. / a1)))
    v2 = math.sqrt(mu * ((2. / r) - (1. / a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(
        ut() + (vessel.orbit.time_to_apoapsis if at_apoapsis else vessel.orbit.time_to_periapsis), prograde=delta_v)

    # Calculate burn time (using rocket equation)
    F = vessel.available_thrust
    Isp = vessel.specific_impulse * vessel.orbit.body.surface_gravity
    m0 = vessel.mass
    m1 = m0 / math.exp(delta_v / Isp)
    flow_rate = F / Isp
    burn_time = abs((m0 - m1) / flow_rate)

    # Orientate ship
    print("Orientating ship for circularisation burn...")
    vessel.control.rcs = rcs
    vessel.auto_pilot.engage()
    vessel.auto_pilot.reference_frame = node.reference_frame
    vessel.auto_pilot.target_direction = (0, 1, 0)
    vessel.auto_pilot.wait()

    # Wait until burn
    print("Waiting until circularization burn...")
    burn_ut = ut() + (vessel.orbit.time_to_apoapsis if at_apoapsis else vessel.orbit.time_to_periapsis) - (
                burn_time / 2.)
    lead_time = 5
    conn.space_center.warp_to(burn_ut - lead_time)

    # Execute burn
    print("Ready to execute burn.")
    time_to = conn.add_stream(getattr, vessel.orbit, ("time_to_apoapsis" if at_apoapsis else "time_to_periapsis"))
    while time_to() - (burn_time / 2.) > 0:
        pass
    print("Executing burn...")
    vessel.control.throttle = 1.0
    end_time = ut() + burn_time
    while (end_time - 0.2) > ut():
        checkFuel()

    print("Fine tuning...")
    vessel.control.throttle = 0.25
    remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
    while remaining_burn()[1] > 2.0:  # 2m/s
        checkFuel()
    vessel.control.throttle = 0.0
    node.remove()


def launch(desired_alt):
    vessel.control.throttle = 1
    stage()
    vessel.auto_pilot.target_pitch_and_heading(90, 90)
    vessel.auto_pilot.engage()
    turn_angle = 0

    while True:
        checkFuel()
        if altitude() > start_gravity_turn and altitude() < end_gravity_turn:
            frac = ((altitude() - start_gravity_turn) /
                    (end_gravity_turn - start_gravity_turn))
            new_turn_angle = frac * 90
            if abs(new_turn_angle - turn_angle) > 0.5:
                print("Setting pitch to {:.1f}...".format(90 - turn_angle))
                turn_angle = new_turn_angle
                vessel.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)
        if apoapsis() > desired_alt * 0.9:
            print("Fine tuning...")
            break

    vessel.control.throttle = 0.25
    while apoapsis() < desired_alt:
        checkFuel()
    vessel.control.throttle = 0.0
    print("Target apoapsis reached!")

    # Wait until out of atmosphere
    print("Coasting out of atmosphere...")
    print(vessel.orbit.body)
    climb_height = 7000
    if(vessel.orbit.body.has_atmosphere):
        climb_height= vessel.orbit.body.atmosphere_depth
    print(climb_height)
    while altitude() < climb_height:
        pass
        
    vessel.control.toggle_action_group(1)
    circularise()

    vessel.auto_pilot.target_direction = (0, 1, 0)
    vessel.auto_pilot.wait()
    vessel.control.sas = True
    print("Launch complete!")


def set_altitude(desired_alt, at_apoapsis=True, rcs=False):
    print("Planning burn...")
    delta_v = hohmann_elliptical((vessel.orbit.apoapsis if at_apoapsis else vessel.orbit.periapsis),
                                 desired_alt + vessel.orbit.body.equatorial_radius)
    node_time = ut() + (vessel.orbit.time_to_periapsis if at_apoapsis else vessel.orbit.time_to_apoapsis)
    node = vessel.control.add_node(node_time, prograde=delta_v)
    F = vessel.available_thrust
    Isp = vessel.specific_impulse * vessel.orbit.body.surface_gravity
    m0 = vessel.mass
    m1 = m0 / math.exp(abs(delta_v) / Isp)
    flow_rate = F / Isp
    burn_time = abs((m0 - m1) / flow_rate)

    # Orientate ship
    print("Orientating ship for burn...")
    vessel.control.rcs = rcs
    vessel.control.throttle = 0
    vessel.auto_pilot.engage()
    vessel.auto_pilot.reference_frame = node.reference_frame
    vessel.auto_pilot.wait()

    # Wait until burn
    print("Waiting until burn...")
    burn_ut = node_time - (burn_time / 2.)
    lead_time = 5
    conn.space_center.warp_to(burn_ut - lead_time)

    # Execute burn
    print("Ready to execute burn.")
    while ut() - (node_time + (burn_time / 2.)) > 0:
        pass
    print("Executing burn...")
    vessel.control.throttle = 1.0
    end_time = ut() + burn_time
    while (end_time - 1) > ut():
        checkFuel()
    print("Fine tuning...")
    vessel.control.throttle = 0.05
    remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
    while ((remaining_burn()[1] > 1.5) or (abs(desired_alt - (apoapsis() if at_apoapsis else periapsis())) > 1000)):
        pass
    vessel.control.throttle = 0.0
    node.remove()
    print("Burn complete...")


def mun_transfer():
    print("Starting transfer...")
    celestial_body = conn.space_center.bodies["Mun"]
    destSemiMajor = celestial_body.orbit.semi_major_axis
    hohmannSemiMajor = destSemiMajor / 2
    neededPhase = 2 * math.pi * (1 / (2 * (destSemiMajor ** 3 / hohmannSemiMajor ** 3) ** (1 / 2)))
    optimalPhaseAngle = 180 - neededPhase * 180 / math.pi

    # Get current phase angle
    phaseAngle = 2 ** 31 - 1  # Big number
    vessel.control.rcs = True
    vessel.auto_pilot.engage()
    vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
    vessel.auto_pilot.target_direction = (0.0, 1.0, 0.0)  # Point pro-grade
    vessel.auto_pilot.wait()
    angleDec = False
    prevPhase = 0

    while abs(phaseAngle - optimalPhaseAngle) > 1 or not angleDec:
        bodyRadius = celestial_body.orbit.radius
        vesselRadius = vessel.orbit.radius
        time.sleep(1)
        bodyPos = celestial_body.orbit.position_at(conn.space_center.ut, celestial_body.reference_frame)
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
        print("Phase: {:.1f}".format(phaseAngle))

    # Use vis-viva to calculate deltaV required to raise orbit to that of the moon
    r = vessel.orbit.radius
    a = vessel.orbit.semi_major_axis
    mu = vessel.orbit.body.gravitational_parameter
    v1 = math.sqrt(mu * ((2 / r) - (1 / a)))
    a = (celestial_body.orbit.radius + vessel.orbit.radius) / 2
    v2 = math.sqrt(mu * ((2 / r) - (1 / a)))
    delta_v = v2 - v1
    print("Maneuver now with deltaV: {:.1f}".format(delta_v))

    actual_delta_v = 0
    vessel.control.throttle = 1.0
    while (delta_v > actual_delta_v):
        time.sleep(0.15)
        r = vessel.orbit.radius
        a = vessel.orbit.semi_major_axis
        actual_delta_v = (mu * ((2 / r) - (1 / a))) ** (1 / 2) - v1
        print("DeltaV so far: {:.1f} out of needed {:.1f}".format(actual_delta_v, delta_v))
        checkFuel()
    vessel.control.throttle = 0
    print("Burn complete.")

    print("Warping...")
    conn.space_center.warp_to(ut() + vessel.orbit.time_to_soi_change + vessel.orbit.next_orbit.time_to_periapsis - 60)

    circularise(False, True)

    print("Lowering to 30,000 metres...")
    vessel.control.rcs = True
    vessel.auto_pilot.engage()
    set_altitude(30000, True)
    circularise(False, True)
    print("Welcome to the Mün!")

def suicide_burn(v_0,d_0,m_0):
    g = vessel.orbit.body.surface_gravity
    delta_v = v_0 +math.sqrt(2*g*d_0)
    F = vessel.available_thrust
    Isp = vessel.specific_impulse * g
    m0 = vessel.mass
    m1 = m0 / math.exp(abs(delta_v) / Isp)
    flow_rate = F / Isp
    burn_time = abs((m0 - m1) / flow_rate)
    print(burn_time)
    return ((delta_v/2)*burn_time,burn_time)

def land_on_mun():
    if(periapsis()>0):
        set_altitude(0,False,False)
    auto_pilot.disengage()
    direction = vessel.flight(vessel.orbital_reference_frame).direction
    auto_pilot.sas = True
    auto_pilot.sas_mode = auto_pilot.sas_mode.retrograde
    auto_pilot.sas = True
    auto_pilot.sas_mode = auto_pilot.sas_mode.retrograde
    safety_constraint = 0.85
    vessel.control.throttle = 0.0
    current_alt = vessel.flight().surface_altitude
    obt_frame = vessel.orbit.body.non_rotating_reference_frame
    orb_speed = conn.add_stream(getattr, vessel.flight(obt_frame), 'speed')
    start_mass = vessel.mass
    while current_alt > 50:
        start_alt = vessel.flight().surface_altitude
        start_vel = orb_speed()
        sb_dist = suicide_burn(start_vel,start_alt,vessel.mass)
        print("SB_DIST",sb_dist)
        while abs(current_alt)>sb_dist[0]:
          current_alt = vessel.flight().surface_altitude
          pass
        end_time = ut() + sb_dist[1]
        while (end_time - 1) > ut():
            vessel.control.throttle = safety_constraint * (vessel.mass / start_mass)
            checkFuel()
        vessel.control.throttle = 0.0
        current_alt = vessel.flight().surface_altitude
        print("Landing...")
    while current_alt > 5:
        current_alt = vessel.flight().surface_altitude
        if orb_speed() > 10:
            vessel.control.throttle = 0.2
        else:
            vessel.control.throttle = 0
    vessel.control.throttle = 0
    print("Landed...")
    auto_pilot.sas = False