import numpy as np
import xarray as xr


class Scanner:
    def __init__(self, filename):
        self.ds = xr.open_dataset(filename)

    # returns (u, v) surface velocity in meters/second, read from the ocean
    # grid point nearest to (lon, lat) at the time nearest to `time`
    def get_velocity(self, time, lon, lat):
        u = self._nearest_valid(self.ds.u, self.ds.lon_u, self.ds.lat_u, time, lon, lat)
        v = self._nearest_valid(self.ds.v, self.ds.lon_v, self.ds.lat_v, time, lon, lat)
        return u, v

    # nearest-neighbor lookup over a curvilinear lon/lat grid, skipping
    # masked/invalid (NaN) cells so a query near the coast doesn't return NaN

    # Brute force is far too inefficent for long term!!


    def _nearest_valid(self, data, lon_grid, lat_grid, time, lon, lat):
        values = data.sel(ocean_time=time, method='nearest').values
        dist_sq = (lon_grid.values - lon)**2 + (lat_grid.values - lat)**2
        dist_sq = np.where(np.isfinite(values), dist_sq, np.inf)
        eta_idx, xi_idx = np.unravel_index(np.argmin(dist_sq), dist_sq.shape)
        return float(values[eta_idx, xi_idx])
