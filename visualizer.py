import pygame
import pymunk.pygame_util


class Visualizer():
    def __init__(self, width, height, fps):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.clock = pygame.time.Clock()
        self.fps = fps

    # draws one frame; returns False if the user closed the window, True otherwise
    def render(self, space, robot):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        # fill the background with white
        self.screen.fill((255,255,255))
        space.debug_draw(self.draw_options)
        c = robot.coords
#            # draw a solid blue circle in the center
#            pygame.draw.circle(self.screen, (0,0,255), np.ceil(c), 5)
#            # draw a line to show orientation
#            pygame.draw.line(self.screen, (0,0,255), np.ceil(c), np.ceil(c+15*np.array([np.cos(robot.angle),np.sin(robot.angle)])), 3)
        # update the display
        pygame.display.flip()
        self.clock.tick(self.fps)
        return True
