from itertools import chain
import math


class Board(object):
    cell_size = 20

    grid_line_color = (0, 0, 0)
    grid_line_width = 1

    start_point_color = (0, 255, 0)
    start_point_radius = 5

    end_point_color = (255, 0, 0)
    end_point_radius = 5

    path_line_color = (0, 0, 255)
    path_line_width = 3

    wall_color = (139, 69, 19)

    def __init__(self, width=30, height=24):
        self.width = width
        self.height = height

        # Coord of start point
        self.start_point = None
        # Coord of end point
        self.end_point = None

        # Top-left coords of 1x1 walls
        self.walls = []
        # List of coords the path leads down
        self.path = []

    def size(self):
        return (self.width * self.cell_size + self.grid_line_width,
                self.height * self.cell_size + self.grid_line_width)

    def is_valid_point(self, x, y):
        return (0 <= x <= self.width and 0 <= y <= self.height)

    def is_valid_path_point(self, x, y):
        return self.is_valid_point(x, y) and (x, y) not in self.walls

    def draw_grid(self, surface):
        width_px = self.width * self.cell_size
        height_px = self.height * self.cell_size

        # We go an extra cell_size to get the outside border
        for x in xrange(0, width_px + self.cell_size, self.cell_size):
            pygame.draw.line(surface, self.grid_line_color,
                             (x, 0), (x, height_px), self.grid_line_width)

        for y in xrange(0, height_px + self.cell_size, self.cell_size):
            pygame.draw.line(surface, self.grid_line_color,
                             (0, y), (width_px, y), self.grid_line_width)

    def draw_start_point(self, surface):
        if self.start_point is None:
            return
        else:
            x, y = self.start_point
            self._draw_circle(surface, x, y,
                              self.start_point_radius, self.start_point_color)

    def draw_end_point(self, surface):
        if self.end_point is None:
            return
        else:
            x, y = self.end_point
            self._draw_circle(surface, x, y,
                              self.end_point_radius, self.end_point_color)

    def draw_path(self, surface):
        if self.start_point is None:
            return
        if len(self.path) < 1:
            return

        last_x, last_y = self.start_point
        for x, y in self.path:
            if not self.is_valid_point(x, y):
                raise ValueError('Invalid path coordinate ({}, {})'.format(x,
                                                                           y))
            source = (last_x * self.cell_size, last_y * self.cell_size)
            dest = (x * self.cell_size, y * self.cell_size)
            pygame.draw.line(surface, self.path_line_color, source, dest,
                             self.path_line_width)

            last_x, last_y = x, y

    def draw_walls(self, surface):
        for c_x, c_y in self.walls:
            if not self.is_valid_point(c_x, c_y):
                raise ValueError('Invalid location ({}, {}) '
                                 'for wall'.format(c_x, c_y))

            rect = pygame.Rect(c_x * self.cell_size - self.cell_size / 2,
                               c_y * self.cell_size - self.cell_size / 2,
                               self.cell_size, self.cell_size)
            pygame.draw.rect(surface, self.wall_color, rect)

    def render(self, surface):
        self.draw_grid(surface)
        self.draw_walls(surface)
        self.draw_path(surface)
        self.draw_start_point(surface)
        self.draw_end_point(surface)

    def _draw_circle(self, surface, x, y, r, color):
        pygame.draw.circle(surface, color, (x * self.cell_size,
                                            y * self.cell_size), r)


class Pathfinder(object):
    """Base class for pathfinders"""

    def __init__(self, board):
        self.board = board
        if self.board.start_point is None:
            raise ValueError('Board has no start point set')
        if self.board.end_point is None:
            raise ValueError('Board has no end point set')

    def __iter__(self):
        return self

    def next(self):
        raise StopIteration


class SimplePathfinder(Pathfinder):
    def __init__(self, board):
        super(SimplePathfinder, self).__init__(board)

        self.x, self.y = self.board.start_point
        self.already_taken = [self.board.start_point]

    def dist_to_end(self, x, y):
        end_x, end_y = self.board.end_point
        return math.sqrt((end_x - x) ** 2 + (end_y - y) ** 2)

    def get_valid_moves(self, x, y):
        moves = []
        if x > 0:
            moves.append((x - 1, y))
        if x < self.board.width:
            moves.append((x + 1, y))
        if y > 0:
            moves.append((x, y - 1))
        if y < self.board.height:
            moves.append((x, y + 1))
        return moves

    def next(self):
        if (self.x, self.y) == self.board.end_point:
            raise StopIteration

        valid_moves = self.get_valid_moves(self.x, self.y)
        new_moves = filter(lambda p: p not in self.already_taken, valid_moves)
        available_moves = filter(lambda p: self.board.is_valid_path_point(*p),
                                 new_moves)

        least_dist = float('Inf')
        least_point = None
        for point in available_moves:
            dist = self.dist_to_end(*point)
            if dist < least_dist:
                least_dist = dist
                least_point = point

        self.already_taken.append(least_point)
        self.x, self.y = least_point
        return least_point


if __name__ == '__main__':
    import os
    import pygame
    pygame.init()

    board = Board()
    board.start_point = (5, 6)
    board.end_point = (23, 18)
    board.walls = [
        (10, 5),
        (10, 6),
        (10, 7),
        (10, 8),
        (10, 9),
        (10, 10),
        (10, 11),
        (10, 12),
        (9, 12),
        (8, 12),
        (7, 12),
        (6, 12),
    ]

    pathfinder = SimplePathfinder(board)

    width, height = board.size()
    padding = 10
    screen = pygame.display.set_mode((width + padding * 2,
                                      height + padding * 2))
    surface = pygame.Surface((width, height))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                os._exit(0)

        surface.fill((255, 255, 255))
        board.render(surface)

        screen.fill((255, 255, 255))
        screen.blit(surface, (padding, padding))

        pygame.display.flip()

        try:
            next_point = pathfinder.next()
        except StopIteration:
            pass
        else:
            pygame.time.wait(100)
            board.path.append(next_point)
