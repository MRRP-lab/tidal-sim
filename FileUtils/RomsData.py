import numpy as np
from scipy.spatial import cKDTree

from FileUtils.OceanData import OceanData
from FileUtils.Scanner import Scanner


class RomsData(OceanData):
    # ROMS curvilinear-grid files (e.g. 6a4d31ff-ff3d-23548.nc). Velocity
    # lookups are delegated to Scanner: nearest valid grid cell, nearest
    # time step. Scanner's u/v run along the grid's own xi/eta axes, so
    # they're rotated to east/north by the grid's `angle` (radians from
    # east to the xi axis, counter-clockwise) at the nearest rho point
    def __init__(self, filename):
        self.scanner = Scanner(filename)
        ds = self.scanner.ds
        self.start_time = ds.ocean_time.values[0]
        self.bounds = (float(ds.lon_rho.min()), float(ds.lon_rho.max()),
                       float(ds.lat_rho.min()), float(ds.lat_rho.max()))

        self.lon_scale = np.cos(np.radians((self.bounds[2] + self.bounds[3])/2))
        self.angle = ds.angle.values.ravel()
        self.mask = ds.mask_rho.values.ravel() # 1 = water, 0 = land
        self.tree = cKDTree(np.column_stack((ds.lon_rho.values.ravel()*self.lon_scale,
                                             ds.lat_rho.values.ravel())))

    def get_start_time(self):
        return self.start_time

    def get_bounds(self):
        return self.bounds

    def get_velocity(self, time, lon, lat):
        u, v = self.scanner.get_velocity(time, lon, lat)
        _, i = self.tree.query((lon*self.lon_scale, lat))
        a = self.angle[i]
        return float(u*np.cos(a) - v*np.sin(a)), float(u*np.sin(a) + v*np.cos(a))

    # whether the nearest rho point is water
    def is_water(self, lon, lat):
        _, i = self.tree.query(np.column_stack((np.ravel(lon)*self.lon_scale, np.ravel(lat))))
        return (self.mask[i] == 1).reshape(np.shape(lon))
