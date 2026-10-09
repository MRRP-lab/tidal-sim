from multiprocessing import connection
import numpy as np
import pygame
import random
import pandas as pd
import os
import glob

import utils

########################## PARAMETERS ###########################################

tag = "test"
SAVE_VID = False
VIZGRID = False
FPS = 10
vid_name = tag+".mp4"
viddir = './videos'
global_filename = "configs/global_config.yaml"
e_filename = "configs/env_config.yaml"

########################## SETUP ##########################

# set up folder for saving frames
if SAVE_VID:
    if not os.path.exists(viddir):
        os.mkdir(viddir)
    vid_out = os.path.join(viddir, vid_name)
    os.makedirs(tag+"_frames")

params = utils.load_config(global_filename)
ss, grid_num = params["screen_size"], params["grid_num"]
obstacles = utils.load_env(e_filename)
width = ss # for vid
height = ss # for vid

# set up env
pygame.init()
screen = pygame.display.set_mode([ss,ss])
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)

# import the data
sim_data = pd.read_csv("data/"+tag+".csv",dtype=float)

x_list = sim_data['x'].to_list()
y_list = sim_data['y'].to_list()
theta_list = sim_data['theta'].to_list()

########################## METHODS  ##########################################

# Stigmergy utils
# Creates array of tuples (x, y, index, stimulus) to represent the corners of the grid
# Main purpose right now is visualizing where robots have been
class Grid():
    def __init__(self, ss, grid_num):
        self.ss = ss
        self.grid_num = grid_num
        self.interval = self.ss/self.grid_num
        self.x_coords = np.arange(0, self.grid_num, dtype = float)
        self.new_grid = np.arange(0, self.grid_num*self.grid_num, dtype = tuple)
        self.perGrid = np.arange(0, self.grid_num*self.grid_num, dtype = int)
        self.robotsPer = {}
        self.prevRobotsPer = {}
        self.changePer = {}
        self.prevShade = {}
        self.fading = {}
        self.initGrid()

    def initGrid(self):
        boxes = self.grid_num**2
        for box in range(boxes):
            self.robotsPer[box] = 0
            self.prevRobotsPer[box] = 0
            self.prevShade[box] = 0
            self.fading[box] = False

    def make_grid(self):
        grid_corners = np.arange(0, self.grid_num*self.grid_num, dtype = tuple)
        index = 0

        for x_vals in range(self.grid_num):
            x = float(x_vals*self.interval)
            self.x_coords[x_vals] = float(x)
            for y_vals in range(self.grid_num):
                y = float(y_vals*self.interval)
                grid_corners[index] = (x, y, index, 0.0)
                index += 1
        new_grid = grid_corners.reshape(grid_num, grid_num)
        self.new_grid = new_grid

        return new_grid

    def shadeFade(self, shade, concentration):
        fadeFactor = 5
        newShade = shade + fadeFactor
        if newShade > 255:
            newShade = 255
        if newShade < 0:
            newShade = 0

        if concentration > 0:
            return newShade
        else:
            return shade

    # Takes in the coordinate that the robot is at, and returns the corresponding number
    # to the box in the grid it is in
    def coord_near(self, robotCoord):
        x_ind = 0
        y_ind = 0

        for x_coord in range(self.grid_num):
            if (robotCoord[0] >= self.new_grid[x_coord][0][0] and \
                robotCoord[0] < self.new_grid[x_coord][0][0]+self.interval):
                x_ind = x_coord

        for y_coord in range(self.grid_num):
            if (robotCoord[1] >= self.new_grid[x_ind][y_coord][1] and \
                robotCoord[1] < self.new_grid[x_ind][y_coord][1]+self.interval):
                y_ind = y_coord

        box = (y_ind*self.grid_num)+x_ind
        return box

    def robotUpdates(self, c):
        self.make_grid()
        boxIn = self.coord_near(c)
        if boxIn in self.robotsPer:
            self.robotsPer[boxIn] += 1
        return self.robotsPer


########################## MAIN  ###########################################

# init
coords = np.array([x_list,y_list]).T
angles = np.array(theta_list)
grid = Grid(ss, grid_num)

# sim loop
framenum = 0
running = True

### Animation Loop
# one frame per logged physics step, so playback always matches the log's length
for time in range(len(sim_data)):
    if(not running):
        break
    # did the user click the close button?
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the background with white
    screen.fill((255,255,255))

    c = coords[time]
    robotsPerGrid = grid.robotUpdates(c)

    for boxes in grid.robotsPer:
            fade = 10
            concentration = grid.robotsPer[boxes]
            shade = 255 - (5*concentration)
            if shade < 0:
                shade = 0

            xHold = boxes%grid.grid_num
            yHold = boxes//grid.grid_num

            x = xHold*grid.interval
            y = yHold*grid.interval

            pygame.draw.rect(screen, (255, shade, 255), (x,y,grid.interval,grid.interval), 0)

    # Draws all of the lines needed to make the grid, prints the box numbers (starting at 1)
    # and draws small dots at all of the intersections of the gridlines
    # Purpose is to help debug grid issues
    if VIZGRID:
        font = pygame.font.SysFont(None, 15)
        for row in range(grid.grid_num):
            inter = 0
            cornerNum = 1
            pt = float(row*grid.interval)
            # draw grid lines
            pygame.draw.line(screen, (255, 0, 0), (pt, 0), (pt, grid.ss), width=1)
            pygame.draw.line(screen, (255, 0, 0), (0, pt), (grid.ss, pt), width=1)

            for column in range(grid.grid_num):
                corner = int(cornerNum + (inter/grid.interval))
                pygame.draw.circle(screen, (255, 0, 0), (pt, inter), 3)

                img = font.render(str((column*grid.grid_num)+row), True, (255, 0, 0))
                screen.blit(img, (pt +5 , inter +5))
                cornerNum += 1
                inter += grid.interval
            #extra row on the far right
            pygame.draw.circle(screen, (255, 0, 0), (grid.ss, pt), 3)
    ############################################################################

    # update robot positions
    c = coords[time]
    # draw a solid blue circle in the center
    pygame.draw.circle(screen, (0,0,255), np.ceil(c), 5)
    # draw a line to show orientation
    pygame.draw.line(screen, (0,0,255), np.ceil(c), np.ceil(c+15*np.array([np.cos(angles[time]),np.sin(angles[time])])), 3)
    # update the display
    pygame.display.flip()
    clock.tick(FPS)

    # save frame to disk
    if SAVE_VID:
        fname = tag + "_frames/%04d.png" % framenum
        pygame.image.save(screen, fname)
        framenum += 1

# quit
pygame.quit()

########################## SAVE TO VID ###########################################

if SAVE_VID:
    cmd = str(f"ffmpeg -r {FPS} -f image2 -i {tag}_frames/%04d.png -y -qscale 0 -s {width}x{height} {vid_out}")
    os.system(cmd)

    # remove frames when done: python should wait...
    # TODO switch to using subprocess lib
    # or maybe pathlib
    files = glob.glob('./'+tag+'_frames/*.png')
    for f in files:
        try:
            os.unlink(f)
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))
            pass

    try:
        os.rmdir('./'+tag+'_frames')
    except OSError as e:
        pass
