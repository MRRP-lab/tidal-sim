import xarray as xr


class GetDT:
    def __init__(self, filename):
        self.ds = xr.open_dataset(filename)

        # `dt` is the model's basic/long time-step (seconds); `dtfast` is a
        # separate, finer internal sub-step — see FileUtils/NCNotes.md
        self.dt = float(self.ds.dt.values)

    def get_dt(self):
        return self.dt


if __name__ == '__main__':
    gd = GetDT("6a4d31ff-ff3d-23548.nc")
    print(gd.get_dt())
