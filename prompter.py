import math
import random


class Prompter:
    # asks in the terminal how long to run the sim, where the boat should
    # spawn and which waypoint it should drive to -- each either a random
    # point on the water or typed coordinates -- and whether to save a log of
    # the run, asking again until each answer is usable. Pressing Enter keeps the
    # default shown in brackets (the value from configs/global_config.yaml)
    #   lon_range, lat_range: (min, max) of usable points, lon in -180..180
    #   on_water(lon, lat): True if the point can be a spawn point or waypoint
    #   default_spawn: (lon, lat), or None for a random water point
    #   default_waypoint: (lon, lat), or None for no waypoint (the boat just drifts)
    #   min_hours: the shortest allowed run (one physics step)
    #   default_log: whether to save the log; log_path: where it would go
    def __init__(self, lon_range, lat_range, on_water, default_hours, default_spawn, default_waypoint,
                 min_hours, default_log, log_path):
        # rounded inward to 3 decimals, so every value in the printed range
        # really is on the map
        self.lon_range = (math.ceil(lon_range[0]*1000)/1000, math.floor(lon_range[1]*1000)/1000)
        self.lat_range = (math.ceil(lat_range[0]*1000)/1000, math.floor(lat_range[1]*1000)/1000)
        self.on_water = on_water
        self.default_hours = default_hours
        self.default_spawn = default_spawn
        self.default_waypoint = default_waypoint
        self.min_hours = min_hours
        self.default_log = default_log
        self.log_path = log_path
        self.rng = random.Random() # unseeded: fresh random points each run

    # returns {"run_hours": hours, "spawn": (lon, lat) or None for random,
    #          "waypoint": (lon, lat) or None for none, "log": True to save the log}
    def ask(self):
        return {"run_hours": self._ask_hours(),
                "spawn": self._ask_point("spawn point", "Spawn the boat at a random point on the water?",
                                         "Where should the boat spawn?", self.default_spawn, "random water point"),
                "waypoint": self._ask_point("waypoint", "Send the boat to a random waypoint on the water?",
                                            "Where should the boat go?", self.default_waypoint, "none, just drift"),
                "log": self._ask_yes_no(f"Save a log of this run to {self.log_path}?", self.default_log)}

    def _ask_hours(self):
        while True:
            text = input(f"How long should the sim run, in hours (e.g. 3 or 0.5)? [{self.default_hours:.3g}]: ").strip()
            if not text:
                return self.default_hours
            try:
                hours = float(text)
            except ValueError:
                print("  That isn't a number -- enter hours, like 3 or 0.5.")
                continue
            if not math.isfinite(hours) or hours < self.min_hours:
                print(f"  It has to be at least {self.min_hours:.3g} hours ({self.min_hours*3600:g} s, one physics step).")
                continue
            return hours

    # a random water point (y), or typed coordinates (n)
    def _ask_point(self, name, random_question, where_question, default, none_text):
        if self._ask_yes_no(random_question, False):
            lon, lat = self._random_point()
            print(f"  Random {name}: {lon}, {lat}")
            return lon, lat
        return self._ask_coordinates(name, where_question, default, none_text)

    # True for y/yes, False for n/no; Enter gives the default
    def _ask_yes_no(self, question, default):
        while True:
            text = input(f"{question} (y/n) [{'y' if default else 'n'}]: ").strip().lower()
            if not text:
                return default
            if text in ("y", "yes"):
                return True
            if text in ("n", "no"):
                return False
            print("  Please answer y or n.")

    # a uniformly random point in the range that's on water, rounded to 4
    # decimals (~10 m) so the printed point can be typed back in to repeat it
    def _random_point(self):
        (lon_min, lon_max), (lat_min, lat_max) = self.lon_range, self.lat_range
        for _ in range(10_000):
            lon = round(self.rng.uniform(lon_min, lon_max), 4)
            lat = round(self.rng.uniform(lat_min, lat_max), 4)
            if self.on_water(lon, lat):
                return lon, lat
        raise ValueError("couldn't find any water on the map to spawn on")

    # default: (lon, lat) kept on Enter, or None, shown as none_text
    def _ask_coordinates(self, name, where_question, default, none_text):
        (lon_min, lon_max), (lat_min, lat_max) = self.lon_range, self.lat_range
        shown = none_text if default is None else f"{default[0]}, {default[1]}"
        print(f"{where_question} Longitude {lon_min:.3f} to {lon_max:.3f}, "
              f"latitude {lat_min:.3f} to {lat_max:.3f}.")
        print("  Format: longitude, latitude in decimal degrees, west negative (e.g. -122.66, 48.65)")
        while True:
            text = input(f"{name[0].upper() + name[1:]} [{shown}]: ").strip()
            if not text:
                return None if default is None else tuple(default)
            try:
                lon, lat = (float(part) for part in text.replace(",", " ").split())
            except ValueError: # not numbers, or not exactly two of them
                print("  Enter two numbers, longitude then latitude, like -122.66, 48.65.")
                continue
            if not (lon_min <= lon <= lon_max and lat_min <= lat <= lat_max):
                print(f"  ({lon}, {lat}) is off the map -- longitude must be {lon_min:.3f} to {lon_max:.3f} "
                      f"and latitude {lat_min:.3f} to {lat_max:.3f}.")
                continue
            if not self.on_water(lon, lat):
                print(f"  ({lon}, {lat}) is on land -- pick a point on the water.")
                continue
            return lon, lat
