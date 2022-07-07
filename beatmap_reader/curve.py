from .enums import CurveType
from typing import Sequence, Union
import math
import numpy as np


class Point:
    def __init__(self, x: float, y: float, anchor_points: bool = False):
        self.x = x
        self.y = y
        self.anchor_point = anchor_points

    def distance_to(self, point):
        return math.sqrt(math.pow(self.x - point.x, 2) + math.pow(self.y - point.y, 2))

    def perpendicular_vector(self, point):
        return Vector(self.y - point.y, point.x - self.x).normalize()

    def slope(self, point):
        if self.x == point.x:
            return
        return (point.y - self.y) / (point.x - self.x)

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y and self.anchor_point == other.anchor_point

    def __add__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Point(self.x + other, self.y + other)
        elif hasattr(other, "x") and hasattr(other, "y"):
            return Point(self.x + other.x, self.y + other.y)
        else:
            raise TypeError(f"Can't add Point with type {type(other)}")

    def __sub__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Point(self.x - other, self.y - other)
        elif hasattr(other, "x") and hasattr(other, "y"):
            return Point(self.x - other.x, self.y - other.y)
        else:
            raise TypeError(f"Can't subtract type {type(other)} from Point")

    def __mul__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Point(self.x * other, self.y * other)
        elif hasattr(other, "x") and hasattr(other, "y"):
            return Point(self.x * other.x, self.y * other.y)
        else:
            raise TypeError(f"Can't multiply Point with type {type(other)}")

    def __truediv__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Point(self.x / other, self.y / other)
        elif hasattr(other, "x") and hasattr(other, "y"):
            return Point(self.x / other.x, self.y / other.y)
        else:
            raise TypeError(f"Can't divide Point by type {type(other)}")

    def __round__(self, n=None):
        return Point(round(self.x, n), round(self.y, n))

    def __getitem__(self, index):
        return [self.x, self.y][index]

    def __iter__(self):
        return iter([self.x, self.y])

    def __str__(self):
        return f"({self.x}, {self.y})"


class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def magnitude(self):
        return math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))

    def normalize(self):
        magnitude = self.magnitude()
        if magnitude == 0:
            return Vector(0, 0)
        return self / magnitude

    def __mul__(self, other):
        return Vector(self.x * other, self.y * other)

    def __truediv__(self, other):
        return Vector(self.x / other, self.y / other)


class Points:
    def __init__(self, points: list[Point]):
        offset = 0
        for i in range(len(points)-1):
            if i+1 >= len(points):
                break
            if points[i] == points[i+1]:
                points[i].anchor_point = True
                points.pop(i+1)
        self.points = points

    def split(self):
        points = [[self.points[0]]]
        for point in self.points[1:]:
            points[-1].append(point)
            if point.anchor_point:
                points.append([point])
        if len(points[-1]) == 1:
            points.pop(-1)
        return points

    def __iter__(self):
        return iter(self.points)

    def __getitem__(self, index):
        return self.points[index]

    def __len__(self):
        return len(self.points)

    def __str__(self):
        return ", ".join(list(map(str, self.points)))

    @classmethod
    def from_string(cls, strings: Sequence[str]):
        return cls(
            list(map(
                lambda string: Point(*tuple(map(
                    int, string.split(":")
                ))),
                strings
            )))


class CurveBase:
    def __init__(self, points: Points, parent):
        self.points = points
        self.parent = parent
        self.radius_offset = (54.4 - 4.48 * self.parent.parent.difficulty.circle_size)
        self.curve_points_cache = None
        self.osu_pixel_multiplier = 1

    def set_multiplier(self, multiplier):
        self.osu_pixel_multiplier = multiplier

    def create_curve_functions(self):
        raise NotImplementedError()

    @property
    def curve_points(self):
        if self.curve_points_cache is None:
            self.create_curve_functions()
        return self.curve_points_cache


class Bezier(CurveBase):
    type = CurveType.BEZIER

    def _get_t_points(self, max_t=1):
        # TODO: limit curve to max length
        return np.linspace(0, max_t, math.ceil(self.parent.length*self.osu_pixel_multiplier))

    def _save_curve_result(self, curves, max_t=1):
        t_points = self._get_t_points(max_t)
        self.curve_points_cache = sum([
            list(map(
                curve,
                t_points
            ))
            for curve in curves
        ], [])

    def _create_curve(self, points):
        if len(points) < 2:
            raise ValueError("Not enough points to create curve")
        if len(points) == 2:
            return lambda t: points[0] * (1 - t) + points[1] * t
        b1 = self._create_curve(points[:len(points)-1])
        b2 = self._create_curve(points[1:])
        return lambda t: b1(t) * (1 - t) + b2(t) * t

    def create_curve_functions(self):
        curves = []
        for points in self.points.split():
            curves.append(self._create_curve(points))
        self._save_curve_result(curves)

    def __init__(self, points, parent):
        super().__init__(points, parent)


class PerfectCircle(CurveBase):
    type = CurveType.PERFECT

    def __init__(self, points, parent):
        super().__init__(points, parent)

        self.radius = None

    def _get_t_points(self, max_t=1):
        return np.linspace(0, max_t, math.ceil(self.radius*2*math.pi*(max_t/1)*self.osu_pixel_multiplier))

    def _save_curve_result(self, curve, max_t=1):
        t_points = self._get_t_points(max_t)
        self.curve_points_cache = list(map(lambda p: tuple(map(round, curve(p))), t_points))

    def create_curve_functions(self):
        p0, p1, p2 = self.points

        def div(a, b):
            try:
                return a / b
            except ZeroDivisionError:
                return 0

        y = div(p1.x**2 + p1.y**2 - p0.x**2 - p0.y**2,
                2*(-(p2.y - p1.y)*div(p1.x - p0.x, p2.x-p1.x) + p1.y - p0.y)) - \
            div((p1.x - p0.x)*(p2.x**2 + p2.y**2 - p1.x**2 - p1.y**2),
                2*(p2.x-p1.x)*(-(p2.y-p1.y)*div(p1.x-p0.x, p2.x-p1.x)+p1.y-p0.y))
        x = div(p2.x**2 + p2.y**2 - p1.x**2 - p1.y**2,
                (2*(p2.x-p1.x))) - \
            div((p2.y - p1.y)*y, p2.x - p1.x)
        m_point = Point(x, y)
        self.radius = math.sqrt((m_point.x-p0.x)**2 + (m_point.y - p0.y)**2)
        start_angle = 2*math.pi-math.atan2(p0.y-m_point.y, p0.x-m_point.x)
        self._save_curve_result(lambda t: (
            (self.radius*math.cos((1-t)*start_angle) + m_point.x),
            (self.radius*math.sin((1-t)*start_angle) + m_point.y)
        ), self.parent.length / (2*math.pi*self.radius))


class Linear(CurveBase):
    type = CurveType.LINEAR

    def __init__(self, points, parent):
        super().__init__(points, parent)

    def _get_t_points(self, lines):
        return [np.linspace(0, 1, math.ceil(line[0].distance_to(line[1])*self.osu_pixel_multiplier)) for line in lines]

    def _save_curve_result(self, line_func, lines, max_t=1):
        t_points = self._get_t_points(lines)
        self.curve_points_cache = sum([
            list(map(
                lambda t: tuple(round(line_func(t, lines[i]))),
                t_points[i]
            ))
            for i in range(len(t_points))],
            []
        )

    def create_curve_functions(self):
        # TODO: limit curve to max length
        lines = [(self.points[i], self.points[i + 1]) for i in range(len(self.points) - 1)]
        self._save_curve_result((lambda t, line: line[0]*(1-t) + line[1]*t), lines)


class CatMull(CurveBase):
    type = CurveType.CATMULL

    def __init__(self, points, parent):
        super().__init__(points, parent)

    def _get_t_points(self, max_t=1):
        # TODO: limit curve to max length
        return np.linspace(0, max_t, math.ceil(self.parent.length*self.osu_pixel_multiplier))

    def _save_curve_result(self, curves, max_t=1):
        t_points = self._get_t_points(max_t)
        self.curve_points_cache = sum([
            list(map(
                curve,
                t_points
            ))
            for curve in curves
        ], [])

    @staticmethod
    def create_t(p0, p1, t0, alpha):
        return math.pow(math.pow(math.pow(p1.x - p0.x, 2) + math.pow(p1.y - p0.y, 2), 0.5), alpha) + t0

    @staticmethod
    def create_a(p0, p1, t0, t1):
        return lambda t: p0 * ((t1-t)/(t1-t0)) + p1 * ((t-t0)/(t1-t0))

    @staticmethod
    def create_b(a0, a1, t0, t1):
        return lambda t: a0(t) * ((t1-t)/(t1-t0)) + a1(t) * ((t-t0)/(t1-t0))

    @staticmethod
    def create_curve(p0, p1, p2, p3):
        def catmull(t):
            t2 = t * t
            t3 = t2 * t
            return round(0.5 *
                         (2 * p1.x +
                          (-p0.x + p2.x) * t +
                          (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 +
                          (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3),
                         ), round(0.5 *
                                  (2 * p1.y +
                                   (-p0.y + p2.y) * t +
                                   (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 +
                                   (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3)
                                  )
        return catmull

    def create_curve_functions(self):
        curves = []
        for i in range(len(self.points)-1):
            p0 = self.points[i] if i == 0 else self.points[i-1]
            p1 = self.points[i]
            p2 = self.points[i+1] if i < len(self.points)-1 else p1 + p1 - p0
            p3 = self.points[i+2] if i < len(self.points)-2 else p2 + p2 - p1
            curves.append(CatMull.create_curve(p0, p1, p2, p3))
        self._save_curve_result(curves)


class Curve:
    def __new__(cls, curve_data, parent) -> Union[Bezier, PerfectCircle, Linear, CatMull]:
        curve_data = curve_data.split("|")
        curve_data.insert(1, f"{parent.x}:{parent.y}")
        type = curve_data[0].upper()
        points = Points.from_string(curve_data[1:])
        return {
            "B": Bezier,
            "P": PerfectCircle,
            "L": Linear,
            "C": CatMull,
        }[type](points, parent)
