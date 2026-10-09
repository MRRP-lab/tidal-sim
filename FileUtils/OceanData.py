from abc import ABC, abstractmethod

import xarray as xr


class OceanData(ABC):
    # one reader per ocean-model file format -- run_sim.py only talks to
    # this interface, so ROMS and FVCOM files are interchangeable

    # first available time step, as a numpy datetime64
    @abstractmethod
    def get_start_time(self):
        ...

    # (lon_min, lon_max, lat_min, lat_max) in the file's own longitude
    # convention: -180..180 for ROMS, 0..360 for SSCOFS/FVCOM
    @abstractmethod
    def get_bounds(self):
        ...

    # (u, v) eastward/northward surface velocity in meters/second at
    # (lon, lat) and `time`
    @abstractmethod
    def get_velocity(self, time, lon, lat):
        ...

    # True where (lon, lat) is water the model covers. Takes arrays (or
    # scalars) and returns a bool array of the same shape
    @abstractmethod
    def is_water(self, lon, lat):
        ...


# picks a reader by sniffing the file's dimensions
def open_ocean_data(filename):
    # imported here, not at the top, since both readers import OceanData
    from FileUtils.FvcomData import FvcomData
    from FileUtils.RomsData import RomsData

    with xr.open_dataset(filename) as ds:
        dims = set(ds.sizes)
    if "nele" in dims:
        return FvcomData(filename)
    if "xi_rho" in dims:
        return RomsData(filename)
    raise ValueError(f"{filename}: not a recognized ROMS or FVCOM file (dimensions: {sorted(dims)})")
