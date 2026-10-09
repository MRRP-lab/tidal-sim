import xarray as xr


class GetDimension:
    def __init__(self, filename):
        self.ds = xr.open_dataset(filename)
        print(self.ds.sizes)
        # xi_* is each grid's column count (X), eta_* is its row count (Y) —
        # see FileUtils/NCNotes.md. The four spatial grids (rho/u/v/psi) are
        # staggered and don't all share the same shape, so take the max of
        # each axis to find a size that covers all of them.
        self.max_x = max(self.ds.sizes[xi] for xi in ("xi_rho", "xi_u", "xi_v", "xi_psi"))
        self.max_y = max(self.ds.sizes[eta] for eta in ("eta_rho", "eta_u", "eta_v", "eta_psi"))

    def get_max_dimensions(self):
        return self.max_x, self.max_y


if __name__ == '__main__':
    gd = GetDimension("6a4d31ff-ff3d-23548.nc")
    print(gd.get_max_dimensions())
