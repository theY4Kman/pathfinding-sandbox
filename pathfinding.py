import math
import os
import random

from queue import PriorityQueueSet

import pygame
pygame.init()


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

    def __init__(self, width=30, height=24, start=None, end=None):
        self.width = width
        self.height = height

        # Coord of start point
        self.start_point = start
        # Coord of end point
        self.end_point = end

        # Top-left coords of 1x1 walls
        self.walls = []
        # List of coords the path leads down
        self.path = []

    def size(self):
        return (self.width * self.cell_size + self.grid_line_width,
                self.height * self.cell_size + self.grid_line_width)

    def is_in_board(self, (x, y)):
        return (0 <= x <= self.width and 0 <= y <= self.height)

    def is_valid_path_point(self, (x, y)):
        return self.is_in_board((x, y)) and not self.is_wall((x, y))

    def is_wall(self, point):
        return point in self.walls

    def get_open_points(self):
        all_points = [(x, y)
                      for x in xrange(self.width)
                      for y in xrange(self.height)]
        return filter(lambda p: not self.is_wall(p), all_points)

    def dist_to_end(self, (x, y)):
        end_x, end_y = self.end_point
        return math.sqrt((end_x - x) ** 2 + (end_y - y) ** 2)

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
            self._draw_circle(surface, (x, y),
                              self.start_point_radius, self.start_point_color)

    def draw_end_point(self, surface):
        if self.end_point is None:
            return
        else:
            x, y = self.end_point
            self._draw_circle(surface, (x, y),
                              self.end_point_radius, self.end_point_color)

    def draw_path(self, surface):
        if self.start_point is None:
            return
        if len(self.path) < 1:
            return

        last_x, last_y = self.start_point
        for x, y in self.path:
            if not self.is_in_board((x, y)):
                raise ValueError('Invalid path coordinate ({}, {})'.format(x,
                                                                           y))
            source = (last_x * self.cell_size, last_y * self.cell_size)
            dest = (x * self.cell_size, y * self.cell_size)
            pygame.draw.line(surface, self.path_line_color, source, dest,
                             self.path_line_width)

            last_x, last_y = x, y

    def draw_walls(self, surface):
        for c_x, c_y in self.walls:
            if not self.is_in_board((c_x, c_y)):
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

    def _draw_circle(self, surface, (x, y), r, color):
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

    def get_valid_moves(self, (x, y)):
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

    def get_available_moves(self, x, y):
        return filter(self.board.is_valid_path_point,
                      self.get_valid_moves((x, y)))

    def __iter__(self):
        return self

    def next(self):
        raise StopIteration


class SimplePathfinder(Pathfinder):
    def __init__(self, board):
        super(SimplePathfinder, self).__init__(board)

        self.x, self.y = self.board.start_point
        self.already_taken = [self.board.start_point]

    def next(self):
        if (self.x, self.y) == self.board.end_point:
            raise StopIteration

        valid_moves = self.get_valid_moves((self.x, self.y))
        new_moves = filter(lambda p: p not in self.already_taken, valid_moves)
        available_moves = filter(self.board.is_valid_path_point, new_moves)

        least_dist = float('Inf')
        least_point = None
        for point in available_moves:
            dist = self.board.dist_to_end(point)
            if dist < least_dist:
                least_dist = dist
                least_point = point

        self.already_taken.append(least_point)
        self.x, self.y = least_point
        return least_point


class BestFirstSearchPathfinder(Pathfinder):
    def __init__(self, *args, **kwargs):
        super(BestFirstSearchPathfinder, self).__init__(*args, **kwargs)
        self.open = PriorityQueueSet()
        self.closed = set()

        # Maps points to their parents
        self.parents = {}

        self.open.put(0, self.board.start_point)

    def trace_parents(self, point):
        path = [point]
        while True:
            try:
                next_point = self.parents[point]
            except KeyError:
                return path[::-1]
            else:
                path.append(next_point)
                point = next_point

    def find_path(self):
        while True:
            dist_traveled, n = self.open.get()
            self.closed.add(n)

            if n == self.board.end_point:
                return self.trace_parents(n)

            for successor in self.get_available_moves(*n):
                if successor not in self.closed and successor not in self.open:
                    self.open.put(dist_traveled + 1, successor)
                    self.parents[successor] = n
                else:
                    successor_prev_dist_traveled = self.open.priority(successor)
                    if dist_traveled + 1 < successor_prev_dist_traveled:
                        parent = self.parents[successor]
                        self.open.replace(dist_traveled + 1, parent)

    def __iter__(self):
        return self.find_path()


class SimpleWallGenerator(object):
    change_direction_chance = 0.3

    def __init__(self, board):
        self.board = board

        self.open_points = board.get_open_points()

    @staticmethod
    def get_random_direction_vector():
        return random.choice([
            (1, 0),
            (0, 1),
            (-1, 0),
            (0, -1),
        ])

    def get_positions_ahead(self, (x, y), direction):
        """Gets the points straight forward and diagonal to the passed point

        -------
        |a|b|c|
        -------  For point 'e', (1,1), and direction right, (1, 0), this will
        |d|e|f|  return ['c', 'f', 'i'], which is [(2, 1), (2, 0), (2, 2)]
        -------
        |g|h|i|
        -------
        """
        if all(direction):
            raise ValueError('direction must be a normalized vector (x, y) '
                             'with either x or y as 1')

        dir_x, dir_y = direction
        if dir_x:
            a_d_x = [dir_x] * 3
        else:
            a_d_x = [-1, 0, 1]

        if dir_y:
            a_d_y = [dir_y] * 3
        else:
            a_d_y = [-1, 0, 1]

        positions = [(x + d_x, y + d_y) for d_x, d_y in zip(a_d_x, a_d_y)]
        return filter(self.board.is_in_board, positions)

    def get_turn_vectors(self, (dir_x, dir_y)):
        if dir_x and dir_y:
            raise ValueError('direction must be a normalized vector (x, y) '
                             'with either x or y as 1')
        if dir_x:
            return [(0, 1), (0, -1)]
        if dir_y:
            return [(1, 0), (-1, 0)]

    def generate_wall(self, point, length):
        direction = self.get_random_direction_vector()
        for _ in xrange(length):
            # Detects if the wall is outside the board. The conflict
            # detection should never allow a wall to be inside another wall
            if point not in self.open_points:
                return

            possible_conflicts = self.get_positions_ahead(point, direction)
            for pos in possible_conflicts:
                if pos not in self.open_points:
                    return

            self.board.walls.append(point)
            self.open_points.remove(point)

            # Change direction
            if random.random() < self.change_direction_chance:
                direction = random.choice(self.get_turn_vectors(direction))

            x, y = point
            d_x, d_y = direction
            point = (x + d_x, y + d_y)

    def build_walls(self):
        # Don't know what to call this arbitrary number related in some way to the
        # size of the board.
        board_alpha = int(math.ceil(math.log(self.board.width
                                             * self.board.height)))
        num_walls = random.randint(board_alpha, board_alpha * 2)

        for _ in xrange(num_walls):
            length = random.randint(board_alpha * 2, board_alpha ** 2)
            point = random.choice(self.open_points)
            self.generate_wall(point, length)


class Sandbox(object):
    padding = 10

    def __init__(self):
        self.reset()
        self.initialize_screen()

    def reset(self):
        self.board = Board(start=(0, 0), end=(30, 24))

        self.wall_gen = SimpleWallGenerator(self.board)
        self.wall_gen.build_walls()

        self.set_start_end_points()

        self.pathfinder = BestFirstSearchPathfinder(self.board)
        self.path_iter = iter(self.pathfinder.find_path())

    def set_start_end_points(self):
        def is_ccw((p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)):
            """Whether 3 points constitute a straight line or "left" turn"""
            ccw = (p2_x - p1_x) * (p3_y - p1_y) - (p2_y - p1_y) * (p3_x - p1_x)
            return ccw >= 0

        def angle((p1_x, p1_y), (p2_x, p2_y)):
            d_x = p2_x - p1_x
            d_y = p2_y - p1_y
            return math.atan2(d_y, d_x)

        def dist((p1_x, p1_y), (p2_x, p2_y)):
            return math.sqrt((p2_x - p1_x) ** 2 + (p2_y - p1_y) ** 2)

        points = self.board.get_open_points()
        # Remove all points on the border, 'cause they're not interesting
        points = filter(lambda (x, y): (x not in (self.board.width, 0)
                                        and y not in (self.board.height, 0)),
                        points)
        points.sort(key=lambda (x, y): (y, x))

        first_point = points[0]
        points = sorted(points[1:], key=lambda p: angle(p, first_point))

        hull = [first_point, points[0]]
        for point in points:
            if is_ccw(*(hull[-2:] + [point])):
                hull.append(point)
            else:
                hull = hull[:-1]

        farthest_points = None
        farthest_distance = -1
        not_measured = hull[:]
        for fixed in hull:
            not_measured.remove(fixed)
            for point in not_measured:
                distance = dist(fixed, point)
                if distance > farthest_distance:
                    farthest_distance = distance
                    farthest_points = (fixed, point)

        self.board.start_point, self.board.end_point = farthest_points

    def initialize_screen(self):
        width, height = self.board.size()
        self.screen = pygame.display.set_mode((width + self.padding * 2,
                                               height + self.padding * 2))
        self.surface = pygame.Surface((width, height))

    def mainloop(self):
        STATE_DRAWING = 0
        STATE_SHOWING = 1

        RESETEVENT = pygame.USEREVENT + 1

        state = STATE_DRAWING

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    os._exit(0)
                elif event.type in (RESETEVENT, pygame.MOUSEBUTTONUP):
                    self.reset()
                    state = STATE_DRAWING
                    # Cancel repeating timer
                    pygame.time.set_timer(RESETEVENT, 0)

            self.surface.fill((255, 255, 255))
            self.board.render(self.surface)

            self.screen.fill((255, 255, 255))
            self.screen.blit(self.surface, (self.padding, self.padding))

            pygame.display.flip()

            if state == STATE_DRAWING:
                try:
                    next_point = self.path_iter.next()
                except StopIteration:
                    pygame.time.set_timer(RESETEVENT, 1000)
                    state = STATE_SHOWING
                else:
                    pygame.time.wait(100)
                    self.board.path.append(next_point)


if __name__ == '__main__':
    sandbox = Sandbox()
    sandbox.mainloop()
