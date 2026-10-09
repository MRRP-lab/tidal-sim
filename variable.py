import numpy as np
from abc import ABC, abstractmethod

import pymunk


class VelocityEffect(ABC):
    # returns the body's new linear velocity. t: sim seconds elapsed; dt:
    # this physics step's length, as passed by pymunk. An effect may also
    # update body.angular_velocity directly (see AngularDrag)
    @abstractmethod
    def apply(self, t, dt, velocity, body):
        ...


class Damping(VelocityEffect):
    def __init__(self, damping):
        self.damping = damping

    def apply(self, t, dt, velocity, body):
        # apply standard damping to stabilize movement
        return velocity * self.damping


# Both drags below are solved implicitly (backward Euler), after pymunk has
# already added that step's forces/torques. That keeps them stable at any dt
# and makes steady speeds -- drifting with the current, cruising under
# constant thrust, turning under constant torque -- come out the same at any
# dt. How quickly the boat gets to those speeds is only accurate when dt is
# small next to the drag's time scale (a few seconds at the default settings)


class Drag(VelocityEffect):
    # quadratic drag on the body's velocity relative to the water, so a body
    # with nothing else pushing it ends up moving with the current. It acts
    # separately along and across the hull, with across lateral_ratio times
    # stronger -- a keel -- so the boat goes where it points instead of
    # sliding sideways. coefficient is per pixel; water gives the water's
    # velocity in pixels/s (see OceanCurrent)
    def __init__(self, coefficient, water, lateral_ratio=1.0):
        self.coefficient = coefficient
        self.water = water
        self.lateral_ratio = lateral_ratio

    def apply(self, t, dt, velocity, body):
        current = self.water.velocity_px(t, *body.position)
        # velocity through the water in the hull's frame: x along, y across
        relative = (velocity - current).rotated(-body.angle)
        along = self._slow(relative.x, self.coefficient, dt)
        across = self._slow(relative.y, self.coefficient*self.lateral_ratio, dt)
        return current + pymunk.Vec2d(along, across).rotated(body.angle)

    # one axis of the implicit step: the new speed s' solves s' + c*dt*|s'|*s' = s
    @staticmethod
    def _slow(s, c, dt):
        return 2*s / (1 + np.sqrt(1 + 4*c*dt*abs(s)))


class AngularDrag(VelocityEffect):
    # rotational drag: spin decays at `rate` per second
    def __init__(self, rate):
        self.rate = rate

    def apply(self, t, dt, velocity, body):
        body.angular_velocity /= 1 + self.rate*dt
        return velocity


class Gravity(VelocityEffect):
    def __init__(self, gravity):
        self.gravity = gravity

    def apply(self, t, dt, velocity, body):
        return velocity + pymunk.Vec2d(0, self.gravity)*dt


class OceanCurrent:
    # the water's surface velocity anywhere in the arena, read from an
    # OceanData file. Not a VelocityEffect itself: Drag uses it as the
    # velocity of the water the boat sits in
    def __init__(self, ocean_data, coord_map):
        self.ocean_data = ocean_data
        self.coord_map = coord_map
        # there's no sim-time <-> calendar-time mapping in this repo (see
        # Units.md) -- anchor t=0 to the file's own first available time
        # step, and treat t as seconds elapsed from there
        self.start_time = ocean_data.get_start_time()

    # (u, v) eastward/northward m/s at pixel (x, y), t sim seconds in
    def at(self, t, x, y):
        lon, lat = self.coord_map.to_lon_lat(x, y)
        time = self.start_time + np.timedelta64(int(round(t*1000)), 'ms')
        return self.ocean_data.get_velocity(time, lon, lat)

    # the same in pixels/s; v flips because pixel y grows southward
    def velocity_px(self, t, x, y):
        u, v = self.at(t, x, y)
        return pymunk.Vec2d(u, -v) / self.coord_map.metres_per_pixel
