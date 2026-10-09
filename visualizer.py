import numpy as np
import pygame
import pymunk.pygame_util

LAND = (222, 214, 196)
WATER = (200, 222, 240)
ARROW = (40, 70, 120)
WAYPOINT = (200, 40, 40)
ARROW_SPACING = 25 # pixels between current arrows
ARROW_SCALE = 25 # arrow length in pixels per m/s of current
ARROW_REFRESH = 60 # sim seconds between re-sampling the arrows


class Visualizer():
    # water: optional (height, width) bool array, True where there's water,
    # drawn as a land/water map. current: optional OceanCurrent, drawn as
    # arrows on the water: a dot at each sample point, a line pointing downstream.
    # waypoint: optional (x, y) in pixels, drawn as a red ring
    def __init__(self, width, height, fps, water=None, current=None, waypoint=None):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.clock = pygame.time.Clock()
        self.fps = fps

        self.background = None
        if water is not None:
            rgb = np.where(water[..., None], WATER, LAND).astype(np.uint8)
            self.background = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))

        self.waypoint = waypoint
        self.current = current
        self.arrows, self.arrows_t = [], None
        if current is not None:
            gx, gy = np.meshgrid(np.arange(ARROW_SPACING/2, width, ARROW_SPACING),
                                 np.arange(ARROW_SPACING/2, height, ARROW_SPACING))
            keep = water[gy.astype(int), gx.astype(int)] if water is not None else np.ones(gx.shape, bool)
            self.arrow_points = list(zip(gx[keep], gy[keep]))

    # draws one frame at sim time t; returns False if the user closed the window, True otherwise
    def render(self, space, robot, t):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        if self.background is not None:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((255,255,255))
        if self.current is not None:
            self._draw_currents(t)
        if self.waypoint is not None:
            pygame.draw.circle(self.screen, WAYPOINT, self.waypoint, 6, 2)
        space.debug_draw(self.draw_options)
        # update the display
        pygame.display.flip()
        self.clock.tick(self.fps)
        return True

    def _draw_currents(self, t):
        if self.arrows_t is None or abs(t - self.arrows_t) >= ARROW_REFRESH:
            self.arrows = [(x, y, *self.current.at(t, x, y)) for x, y in self.arrow_points]
            self.arrows_t = t
        for x, y, u, v in self.arrows:
            # v flips because pixel y grows southward
            pygame.draw.line(self.screen, ARROW, (x, y), (x + u*ARROW_SCALE, y - v*ARROW_SCALE), 1)
            pygame.draw.circle(self.screen, ARROW, (x, y), 1)
