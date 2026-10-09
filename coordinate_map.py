import numpy as np


# metres per degree of latitude, from a mean Earth radius of 6371 km
METRES_PER_LAT_DEGREE = 111_195


class CoordinateMap:
    # maps simulation pixels to the ocean file's lon/lat with an
    # equirectangular projection over the file's bounding box. Pixel (0, 0)
    # is the north-west corner and y grows southward, matching pymunk's
    # pygame drawing (positive_y_is_up = False). The box's longer side is
    # fixed at `long_side` pixels and the other is sized to keep real
    # proportions: a degree of longitude spans cos(latitude) times the
    # distance of a degree of latitude
    def __init__(self, bounds, long_side):
        self.lon_min, lon_max, lat_min, self.lat_max = bounds
        self.lon_scale = np.cos(np.radians((lat_min + self.lat_max)/2))
        span_x = (lon_max - self.lon_min)*self.lon_scale # in degrees of latitude
        span_y = self.lat_max - lat_min
        self.pixels_per_lat_degree = long_side / max(span_x, span_y)
        self.width = int(round(span_x*self.pixels_per_lat_degree))
        self.height = int(round(span_y*self.pixels_per_lat_degree))
        self.metres_per_pixel = METRES_PER_LAT_DEGREE / self.pixels_per_lat_degree

    def to_lon_lat(self, x, y):
        lon = self.lon_min + x/(self.pixels_per_lat_degree*self.lon_scale)
        lat = self.lat_max - y/self.pixels_per_lat_degree
        return lon, lat

    def to_pixels(self, lon, lat):
        x = (lon - self.lon_min)*self.pixels_per_lat_degree*self.lon_scale
        y = (self.lat_max - lat)*self.pixels_per_lat_degree
        return x, y
