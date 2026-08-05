import numpy as np
import pandas as pd
import random
import time
import os
import pymunk

# custom imports
import utils
from robot import *
from visualizer import Visualizer
from vector_field import VectorField
from variable import Damping, Gravity, OceanCurrent, Drag
from FileUtils.GetDimension import GetDimension
from FileUtils.GetDT import GetDT
from FileUtils.Scanner import Scanner

## PARAMETERS

tag = "test" # change to save data under unique name
VIZ = True
nc_filename = "6a4d31ff-ff3d-23548.nc"

## GLOBAL STATE

# track global time to enable time-varying vector field
sim_state = {
    "time": 0.0
}

## METHODS

def run():
    # Initialize parameters
    global_filename = "configs/global_config.yaml"

    datadir = './data'
    if not os.path.exists(datadir):
        os.mkdir(datadir)

    # load configs
    gparams = utils.load_config(global_filename)
    sim_time, FPS = gparams["sim_time"], gparams["FPS"]

    # arena dimensions come from the .nc file's grid, not configs/global_config.yaml
    width, height = GetDimension(nc_filename).get_max_dimensions()

    # timing: dt comes from the .nc file's own model time-step, not FPS
    dt = GetDT(nc_filename).get_dt()

    # set up environment
    space = pymunk.Space()
    space.gravity = 0, 0 # no gravity: top-down view

    # generate boundary walls sized to (width, height); same shape/thickness
    # convention as the old configs/env_config.yaml obstacles (no longer used)
    wall_thickness = 10
    obs = [
        [[0, 0], [width, 0], [width, wall_thickness], [0, wall_thickness]],
        [[0, 0], [0, height], [wall_thickness, height], [wall_thickness, 0]],
        [[width, height], [0, height], [0, height - wall_thickness], [width, height - wall_thickness]],
        [[width, height], [width, 0], [width - wall_thickness, 0], [width - wall_thickness, height]],
    ]
    for poly in obs:
        # shift coordinates to be centered at zero
        polynp = np.array(poly)
        center = polynp.mean(axis=0)
        genpoly = (polynp - center).tolist()
        shape = pymunk.Poly(space.static_body, genpoly)
        # shift polygon body back to intended location
        shape.body.position = center.tolist()
        space.add(shape)

    # spawn robots
    robot = Robot(global_filename, width=width, height=height)
    robot.body.velocity = [gparams["robot_vel"],0.] # initial velocity vector
    vector_field = VectorField(sim_state)
    scanner = Scanner(nc_filename)
    drag_coefficient = 0.001 # placeholder, not sourced from anywhere -- tune as needed
    vector_field.add(Damping(space.damping))
    vector_field.add(OceanCurrent(scanner, dt))
    vector_field.add(Gravity(space.gravity.y, dt))
    vector_field.add(Drag(drag_coefficient))
    robot.body.velocity_func = vector_field # set custom velocity function
    space.add(robot.body, robot.shape)

    # set up sim and vizualization
    sim_data = [] # for logging data
    if VIZ:
        visualizer = Visualizer(width, height, FPS)

    ### Simulation Loop

    for t in range(int(sim_time/dt)):

        # update robot positions
        space.step(dt)
        sim_state["time"] += dt
        robot.update_state()

        # log position data for replay_sim
        sim_data.append([robot.coords[0], robot.coords[1], robot.angle])

        if VIZ:
            running = visualizer.render(space, robot)
            if not running:
                break

    data = pd.DataFrame(data = sim_data, columns = ["x","y","theta"])
    outdat = os.path.join(datadir, tag+".csv")
    data.to_csv(outdat)

if __name__ == '__main__':
    run()
