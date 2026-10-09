import numpy as np

import utils
from robot_body_builder import Robot_Body_Builder

class Robot():
    # position: pixels. angle: pymunk radians, 0 = bow pointing east,
    # increasing clockwise on screen (pixel y grows southward)
    def __init__(self, filename, position, angle):

        # load parameters
        rconfig = utils.load_config(filename)

        self.coords = np.array(position, dtype=float)
        self.angle = angle

        # robot design parameters
        self.max_vel            = float(rconfig["robot_vel"])
        self.noise_factor       = float(rconfig["noise_factor"])


        # body physics
        builder = Robot_Body_Builder()
        self.body, self.shape = builder.ellipse((self.coords[0], self.coords[1]))
        self.body.angle = angle

    def update_state(self):
        self.coords = (self.body.position.x, self.body.position.y)
        self.angle = self.body.angle

