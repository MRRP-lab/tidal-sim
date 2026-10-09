import numpy as np
import xarray as xr
from scipy.spatial import cKDTree


class Scanner:
    def __init__(self, filename):
        self.ds = xr.open_dataset(filename)
        self.times = self.ds.indexes["ocean_time"]
        # per variable: (time index, its valid values, KD-tree over their
        # lon/lat) for the time step last looked up. The land mask shifts
        # slightly between time steps, so the tree is rebuilt per time step
        self._cache = {}

    # returns (u, v) surface velocity in meters/second, read from the ocean
    # grid point nearest to (lon, lat) at the time nearest to `time`. These
    # run along the grid's own xi/eta axes, not east/north -- RomsData
    # rotates them
    def get_velocity(self, time, lon, lat):
        k = int(self.times.get_indexer([time], method='nearest')[0])
        u = self._nearest_valid("u", self.ds.lon_u, self.ds.lat_u, k, lon, lat)
        v = self._nearest_valid("v", self.ds.lon_v, self.ds.lat_v, k, lon, lat)
        return u, v

    # nearest-neighbor lookup over a curvilinear lon/lat grid, skipping
    # masked/invalid (NaN) cells so a query near the coast doesn't return NaN
    def _nearest_valid(self, name, lon_grid, lat_grid, k, lon, lat):
        if self._cache.get(name, (None,))[0] != k:
            values = self.ds[name].isel(ocean_time=k).values.ravel()
            valid = np.flatnonzero(np.isfinite(values))
            tree = cKDTree(np.column_stack((lon_grid.values.ravel()[valid],
                                            lat_grid.values.ravel()[valid])))
            self._cache[name] = (k, values[valid], tree)
        _, values, tree = self._cache[name]
        _, i = tree.query((lon, lat))
        return float(values[i])
