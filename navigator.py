import math

import pymunk


class Navigator:
    # drives the boat toward a waypoint. Each step it measures where the
    # waypoint is relative to the boat, gets throttle and steering from the
    # PID, and hands those to the motor. Both PID loops hold a setpoint of 0
    # (PID error = setpoint - measurement), so each measurement is how far
    # the boat is off:
    #   power: overshoot -- how far the waypoint is *behind* the bow along the
    #     heading, in pixels (negative while it's still ahead, which gives
    #     forward throttle; positive once passed, which gives reverse)
    #   steer: heading offset -- how far clockwise of the waypoint the bow
    #     points, in degrees, -180..180 so the boat always turns the short way
    # There's no anti-windup, so it can overshoot the waypoint
    def __init__(self, pid, motor, waypoint):
        self.pid = pid
        self.motor = motor
        self.waypoint = pymunk.Vec2d(*waypoint) # pixels
        self.throttle = self.steering = 0.0 # last commands, for logging

    def distance(self, body):
        return (self.waypoint - body.position).length

    def update(self, body, dt):
        to_waypoint = self.waypoint - body.position
        bow = pymunk.Vec2d(1, 0).rotated(body.angle)
        overshoot = -to_waypoint.dot(bow)
        # get_angle_between is positive when the waypoint is clockwise of the bow
        heading_offset = -math.degrees(bow.get_angle_between(to_waypoint))
        throttle = self.pid.power(overshoot, dt)
        steering = self.pid.steer(heading_offset, dt)
        self.throttle, self.steering = self.motor.apply(body, throttle, steering)
