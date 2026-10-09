# generic single-loop PID math, kept private -- PID (below) composes two of
# these internally (one for power, one for steer) rather than duplicating
# this formula twice
class _PIDLoop:
    def __init__(self, kp, ki, kd, setpoint=0.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.integral = 0.0
        self.previous_error = 0.0

    def update(self, measurement, dt):
        error = self.setpoint - measurement
        self.integral += error*dt
        derivative = (error - self.previous_error)/dt if dt > 0 else 0.0
        self.previous_error = error
        return self.kp*error + self.ki*self.integral + self.kd*derivative


class PID:
    # PID controller for the boat, with two independent loops built in:
    # power and steer, computed once per time interval. Power is meant to
    # move the boat's velocity along the vector it's already pointing in
    # (from its current orientation), the way a real boat engine only
    # pushes it forward along its own heading rather than in an arbitrary
    # direction. Steer is meant to rotate that heading vector left or right.
    # This class is only the error-in/control-out math: navigator.py feeds it
    # the boat's position relative to a waypoint, and motor.py turns its
    # outputs into forces on the boat.

    def __init__(self, power_kp, power_ki, power_kd, steer_kp, steer_ki, steer_kd,
                 power_setpoint=0.0, steer_setpoint=0.0):
        self.power_loop = _PIDLoop(power_kp, power_ki, power_kd, power_setpoint)
        self.steer_loop = _PIDLoop(steer_kp, steer_ki, steer_kd, steer_setpoint)

    def power(self, measurement, dt):
        return self.power_loop.update(measurement, dt)

    def steer(self, measurement, dt):
        return self.steer_loop.update(measurement, dt)
