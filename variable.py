import numpy as np
from abc import ABC, abstractmethod

import pymunk


class VelocityEffect(ABC):
    @abstractmethod
    def apply(self, t, velocity, body):
        ...


class Damping(VelocityEffect):
    def __init__(self, damping):
        self.damping = damping

    def apply(self, t, velocity, body):
        # apply standard damping to stabilize movement
        return velocity * self.damping


class Drag(VelocityEffect):
    def __init__(self, coefficient):
        self.coefficient = coefficient

    # standard drag: opposes motion, scales with speed, so the reduction
    # grows quadratically with speed rather than being a constant fraction
    def apply(self, t, velocity, body):
        speed = velocity.length
        return velocity * max(0, 1 - self.coefficient*speed)


class Gravity(VelocityEffect):
    def __init__(self, gravity, dt):
        self.gravity = gravity
        self.dt = dt

    def apply(self, t, velocity, body):
        return velocity + pymunk.Vec2d(0, self.gravity)*self.dt


class OceanCurrent(VelocityEffect):
    def __init__(self, scanner, dt):
        self.scanner = scanner
        self.dt = dt
        # there's no sim-time <-> calendar-time mapping in this repo (see
        # Units.md) -- anchor t=0 to the file's own first available time
        # step, and treat t as seconds elapsed from there
        self.start_time = scanner.ds.ocean_time.values[0]

    def apply(self, t, velocity, body):
        # body.position is in simulation pixels, not real longitude/latitude
        # -- there's no position conversion either (see Units.md), so this
        # is passed straight through to get_velocity as-is
        lon, lat = body.position
        time = self.start_time + np.timedelta64(int(t), 's')
        u, v = self.scanner.get_velocity(time, lon, lat)
        return velocity + pymunk.Vec2d(u, v)*self.dt
