import numpy as np
import random
import pymunk

import utils
import environment
from robot_body_builder import Robot_Body_Builder

class Robot():
    def __init__(self, filename, width=None, height=None):

        # load parameters
        rconfig = utils.load_config(filename)
        # width/height default to configs/global_config.yaml's screen_size
        # (a square arena) unless explicitly overridden, e.g. by run_sim.py
        # sizing the arena from GetDimension instead
        self.width = int(width) if width is not None else int(rconfig["screen_size"])
        self.height = int(height) if height is not None else int(rconfig["screen_size"])
        self.env = environment.Environment(self.width)

        # set up coordinates
        rng = np.random.default_rng()
        coords = [rng.choice(np.arange(self.width)), rng.choice(np.arange(self.height))]
        self.coords = np.array(coords, dtype=float)
        self.disp_coords = np.array(coords, dtype=int)
        self.v = rconfig["robot_vel"]
        self.angle = np.random.random()*2*np.pi

        # robot design parameters
        self.max_vel            = float(rconfig["robot_vel"])
        self.noise_factor       = float(rconfig["noise_factor"])


        # body physics
        builder = Robot_Body_Builder()
        self.body, self.shape = builder.ellipse((self.coords[0], self.coords[1]))

    def update_state(self):
        self.coords = (self.body.position.x, self.body.position.y)
        self.angle = self.body.angle


