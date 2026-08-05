import math

import pymunk


class Robot_Body_Builder:
    # the circle body/shape used everywhere so far
    def standard(self, position):
        mass = 1
        radius = 5
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass=mass, moment=moment)
        body.position = position
        shape = pymunk.Circle(body, radius=radius)
        return body, shape

    # a small ellipse (elongated like a hull, not just a scaled circle) --
    # pymunk has no native ellipse shape, so this is approximated as a
    # many-sided polygon sampled around the ellipse's circumference
    def ellipse(self, position):
        mass = 1
        semi_major = 8 # bow-to-stern half-length
        semi_minor = 3 # half-width (beam)
        num_points = 16
        vertices = [
            (semi_major*math.cos(2*math.pi*i/num_points), semi_minor*math.sin(2*math.pi*i/num_points))
            for i in range(num_points)
        ]
        moment = pymunk.moment_for_poly(mass, vertices)
        body = pymunk.Body(mass=mass, moment=moment)
        body.position = position
        shape = pymunk.Poly(body, vertices)
        return body, shape
