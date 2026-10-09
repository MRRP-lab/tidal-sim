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
from variable import AngularDrag, Drag, OceanCurrent
from coordinate_map import CoordinateMap
from FileUtils.OceanData import open_ocean_data
from prompter import Prompter
from set_variables import SetVariables
from motor import Motor
from navigator import Navigator
from PID import PID

## PARAMETERS

tag = "test" # change to save data under unique name
VIZ = True
PROMPT = True # ask for the run length and spawn point at startup; False runs straight from the config
nc_filename = "6ac83e77-5549-12827.nc"

## GLOBAL STATE

# track global time to enable time-varying vector field
sim_state = {
    "time": 0.0
}

## METHODS

# config longitudes are -180..180; some ocean files (SSCOFS) use 0..360
def to_file_lon(lon, file_bounds):
    return lon + 360 if file_bounds[1] > 180 and lon < 0 else lon

def to_std_lon(lon):
    return (lon + 180) % 360 - 180

def run():
    # Initialize parameters
    global_filename = "configs/global_config.yaml"

    datadir = './data'
    if not os.path.exists(datadir):
        os.mkdir(datadir)

    # load configs
    gparams = utils.load_config(global_filename)
    FPS, dt = gparams["FPS"], gparams["dt"]

    # arena is the configured lon/lat region (or the ocean file's whole
    # extent), with its longer side fixed at screen_size pixels and real
    # proportions kept (see coordinate_map.py)
    ocean_data = open_ocean_data(nc_filename)
    file_bounds = ocean_data.get_bounds()
    if gparams["region"] is None:
        bounds = file_bounds
    else:
        lon_min, lon_max, lat_min, lat_max = gparams["region"]
        bounds = (to_file_lon(lon_min, file_bounds), to_file_lon(lon_max, file_bounds), lat_min, lat_max)
        if not (file_bounds[0] <= bounds[0] < bounds[1] <= file_bounds[1]
                and file_bounds[2] <= bounds[2] < bounds[3] <= file_bounds[3]):
            raise ValueError(f"region {gparams['region']} isn't inside {nc_filename} "
                             f"(extent {file_bounds}); set region: null to use the whole file")
    coord_map = CoordinateMap(bounds, gparams["screen_size"])
    width, height = coord_map.width, coord_map.height

    # which pixels are water, sampled at pixel centers
    xs, ys = np.meshgrid(np.arange(width) + 0.5, np.arange(height) + 0.5)
    water = ocean_data.is_water(*coord_map.to_lon_lat(xs, ys))

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
        # each wall gets its own static body, placed at the wall's center --
        # sharing space.static_body would draw every wall at the last wall's
        # position, and collide there too after any space.reindex_static()
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = center.tolist()
        shape = pymunk.Poly(body, genpoly)
        space.add(body, shape)

    # spawns must be on water and clear of the walls
    margin = wall_thickness + 8 # + the hull's half-length (robot_body_builder.ellipse)
    def on_water(lon, lat):
        x, y = coord_map.to_pixels(to_file_lon(lon, file_bounds), lat)
        return margin <= x < width - margin and margin <= y < height - margin and water[int(y), int(x)]

    # ask the user for the run length and spawn point, keep their answers,
    # and apply them on top of the config
    if PROMPT:
        west, north = coord_map.to_lon_lat(margin, margin)
        east, south = coord_map.to_lon_lat(width - margin, height - margin)
        prompter = Prompter((to_std_lon(west), to_std_lon(east)), (south, north), on_water,
                            default_hours=gparams["sim_time"]/3600, default_spawn=gparams["start"],
                            default_waypoint=gparams["waypoint"], min_hours=dt/3600, default_log=gparams["log"],
                            log_path=os.path.join(datadir, tag+".csv"))
        user_settings = prompter.ask()
        SetVariables(gparams).apply(user_settings)
    sim_time, log = gparams["sim_time"], gparams["log"]

    # spawn: the configured lon/lat, or (start: null) a random water point
    # clear of the walls, drawn from the seed
    if gparams["start"] is not None:
        start_lon, start_lat = gparams["start"]
        if not on_water(start_lon, start_lat):
            raise ValueError(f"start {gparams['start']} isn't on water inside the arena, clear of the walls")
        x, y = coord_map.to_pixels(to_file_lon(start_lon, file_bounds), start_lat)
        heading = gparams["start_heading"]
    else:
        rng = np.random.default_rng(gparams["seed"])
        if not water[margin:height - margin, margin:width - margin].any():
            raise ValueError("the arena has no water to spawn in")
        while True:
            x, y = rng.uniform(margin, width - margin), rng.uniform(margin, height - margin)
            if water[int(y), int(x)]:
                break
        heading = rng.uniform(0, 360)
    # compass heading (clockwise from north) -> pymunk angle (0 = east, y down)
    robot = Robot(global_filename, position=(x, y), angle=np.radians(heading - 90))
    robot.body.velocity = [0., 0.] # starts at rest; drag brings it up to the current's speed

    # the water moves the boat only through drag: the boat is pulled toward
    # the current's velocity rather than being pushed by it directly
    current = OceanCurrent(ocean_data, coord_map)
    vector_field = VectorField(sim_state)
    # drag_coefficient is per metre in the config; the sim works in pixels
    vector_field.add(Drag(gparams["drag_coefficient"]*coord_map.metres_per_pixel, current,
                          gparams["lateral_drag_ratio"]))
    vector_field.add(AngularDrag(gparams["angular_drag"]))
    robot.body.velocity_func = vector_field # set custom velocity function
    space.add(robot.body, robot.shape)

    # with a waypoint, the PID steers the boat to it through the motor;
    # without one, the motor stays off and the boat just drifts
    navigator, waypoint = None, None
    if gparams["waypoint"] is not None:
        wp_lon, wp_lat = gparams["waypoint"]
        if not on_water(wp_lon, wp_lat):
            raise ValueError(f"waypoint {gparams['waypoint']} isn't on water inside the arena, clear of the walls")
        waypoint = coord_map.to_pixels(to_file_lon(wp_lon, file_bounds), wp_lat)
        pid = PID(gparams["power_kp"], gparams["power_ki"], gparams["power_kd"],
                  gparams["steer_kp"], gparams["steer_ki"], gparams["steer_kd"])
        motor = Motor(gparams["forward_force"], gparams["reverse_force"], gparams["steering_force"],
                      stern_offset=8) # the hull's half-length (robot_body_builder.ellipse)
        navigator = Navigator(pid, motor, waypoint)

    # set up sim and vizualization
    # one row per step, plus the spawn at t=0. t is sim seconds; x, y, vx, vy
    # are pixels (y grows southward); theta is pymunk's angle in radians
    # (replay_sim draws with it), heading the same as compass degrees;
    # lon/lat are -180..180; current_u/current_v are the east/north m/s of
    # the water at the boat's position at time t; throttle/steering are the
    # motor commands used during the step (-1..1) and waypoint_dist the
    # pixels left to the waypoint after it (all blank with no waypoint)
    sim_data = []
    def log_row():
        x, y = robot.coords
        lon, lat = coord_map.to_lon_lat(x, y)
        heading = (np.degrees(robot.angle) + 90) % 360
        control = [np.nan]*3 if navigator is None else \
                  [navigator.throttle, navigator.steering, navigator.distance(robot.body)]
        sim_data.append([sim_state["time"], x, y, robot.angle, heading, to_std_lon(lon), lat,
                         *robot.body.velocity, *current.at(sim_state["time"], x, y), *control])
    robot.update_state()
    if log:
        log_row()
    if VIZ:
        visualizer = Visualizer(width, height, FPS, water, current, waypoint)
    closest = (np.inf, 0.0) # nearest the boat got to the waypoint: (pixels, t)

    ### Simulation Loop

    for t in range(int(sim_time/dt)):

        # set this step's motor forces, then update robot positions
        if navigator is not None:
            navigator.update(robot.body, dt)
        space.step(dt)
        sim_state["time"] += dt
        robot.update_state()
        if navigator is not None:
            closest = min(closest, (navigator.distance(robot.body), sim_state["time"]))
        if log:
            log_row()

        if VIZ:
            running = visualizer.render(space, robot, sim_state["time"])
            if not running:
                break

    outdat = os.path.join(datadir, tag+".csv")
    if log:
        data = pd.DataFrame(data = sim_data, columns = ["t","x","y","theta","heading","lon","lat",
                                                        "vx","vy","current_u","current_v",
                                                        "throttle","steering","waypoint_dist"])
        data.to_csv(outdat)
    # the window closes as soon as the run ends, so say that it finished
    print(f"Run finished at t = {sim_state['time']:g} s ({sim_state['time']/3600:.3g} h); "
          + (f"log saved to {outdat}" if log else "no log saved"))
    if navigator is not None:
        print(f"Closest to the waypoint: {closest[0]:.1f} px ({closest[0]*coord_map.metres_per_pixel:.0f} m) "
              f"at t = {closest[1]:g} s; {navigator.distance(robot.body):.1f} px away at the end")

if __name__ == '__main__':
    run()
