import numpy as np
import xarray as xr
from scipy.spatial import cKDTree

from FileUtils.OceanData import OceanData


class FvcomData(OceanData):
    # FVCOM unstructured-mesh files (e.g. full-SSCOFS.nc). u/v live at
    # triangle centers (lonc, latc). "3D Full Profile" files have 10 sigma
    # depth layers, and layer 0 is the surface (siglay runs from -0.016 at the
    # top to -0.93 at the bottom); "Surface Only" files have no siglay at all
    SURFACE = 0

    def __init__(self, filename):
        self.ds = xr.open_dataset(filename)
        self.times = self.ds.time.values
        self.start_time = self.times[0]
        self.bounds = (float(self.ds.lon.min()), float(self.ds.lon.max()),
                       float(self.ds.lat.min()), float(self.ds.lat.max()))

        # a degree of longitude is cos(latitude) times shorter than a degree
        # of latitude, so lon is scaled before building the tree -- otherwise
        # "nearest" would be skewed east-west
        self.lon_scale = np.cos(np.radians((self.bounds[2] + self.bounds[3])/2))
        lonc, latc = self.ds.lonc.values, self.ds.latc.values
        self.tree = cKDTree(np.column_stack((lonc*self.lon_scale, latc)))

        # each triangle's three corners, in the same scaled lon/lat as the
        # tree, for point-in-mesh tests. nv's node numbers are 1-based
        nv = self.ds.nv.values.T - 1
        lon_n, lat_n = self.ds.lon.values*self.lon_scale, self.ds.lat.values
        self.corners = np.stack([np.column_stack((lon_n[nv[:, k]], lat_n[nv[:, k]]))
                                 for k in range(3)], axis=1)

        # surface u/v for the two snapshots bracketing the current time,
        # reloaded only when the sim crosses into the next hour
        self._pair_index = None
        self._pair = None

    def get_start_time(self):
        return self.start_time

    def get_bounds(self):
        return self.bounds

    # nearest triangle, linearly interpolated between hourly snapshots
    def get_velocity(self, time, lon, lat):
        _, elem = self.tree.query((lon*self.lon_scale, lat))
        i, w = self._bracket(time)
        u, v = self._surface_pair(i)
        return (float((1 - w)*u[0, elem] + w*u[1, elem]),
                float((1 - w)*v[0, elem] + w*v[1, elem]))

    # water = inside one of the mesh's triangles. Only the triangles with
    # the 12 nearest centers are tested: 8 already matched testing every
    # triangle, on 3000 random points around Bellingham Bay
    def is_water(self, lon, lat):
        q = np.column_stack((np.ravel(lon)*self.lon_scale, np.ravel(lat)))
        _, idx = self.tree.query(q, k=12)
        a, b, c = (self.corners[idx, k] for k in range(3))
        v0, v1, v2 = c - a, b - a, q[:, None, :] - a
        d00, d01, d11 = (v0*v0).sum(-1), (v0*v1).sum(-1), (v1*v1).sum(-1)
        d20, d21 = (v2*v0).sum(-1), (v2*v1).sum(-1)
        den = d00*d11 - d01*d01
        s = (d11*d20 - d01*d21)/den # barycentric weights toward c and b
        t = (d00*d21 - d01*d20)/den
        eps = 1e-9
        inside = ((s >= -eps) & (t >= -eps) & (s + t <= 1 + eps)).any(axis=1)
        return inside.reshape(np.shape(lon))

    # index i and weight w such that time = (1-w)*times[i] + w*times[i+1],
    # clamped to the file's first and last snapshots
    def _bracket(self, time):
        if time <= self.times[0]:
            return 0, 0.0
        if time >= self.times[-1]:
            return len(self.times) - 2, 1.0
        i = int(np.searchsorted(self.times, time, side='right')) - 1
        w = (time - self.times[i]) / (self.times[i + 1] - self.times[i])
        return i, float(w)

    def _surface_pair(self, i):
        if i != self._pair_index:
            snap = self.ds[["u", "v"]].isel(time=[i, i + 1])
            if "siglay" in snap.sizes:
                snap = snap.isel(siglay=self.SURFACE)
            self._pair = (snap.u.values, snap.v.values)
            self._pair_index = i
        return self._pair
