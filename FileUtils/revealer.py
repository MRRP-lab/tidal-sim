import xarray as xr


class Revealer:
    def __init__(self, filename):
        self.ds = xr.open_dataset(filename)

    # prints every variable in the dataset, sliced to a single ocean_time step
    def print_at_time(self, time_index=0):
        snapshot = self.ds.isel(ocean_time=time_index)
        for name, data in snapshot.variables.items():
            print(name)
            print(data.values)
            print()


if __name__ == '__main__':
    revealer = Revealer("6a4d31ff-ff3d-23548.nc")
    revealer.print_at_time()
