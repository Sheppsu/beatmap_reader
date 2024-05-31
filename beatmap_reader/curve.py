from .enums import CurveType
from typing import Sequence, Union
import math
import numpy as np


class Point:
    __slots__ = ("x", "y", "anchor_point")

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

    def v(self):
        return Vector(self.x, self.y)

    @staticmethod
    def _get_x_y(obj):
        if isinstance(obj, int) or isinstance(obj, float):
            return obj, obj
        elif hasattr(obj, "x") and hasattr(obj, "y"):
            return obj.x, obj.y
        elif hasattr(obj, "__getitem__"):
            return obj[0], obj[1]
        else:
            raise TypeError(f"Can't get x and y from type {type(obj)}")

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y and self.anchor_point == other.anchor_point

    def __add__(self, other):
        x, y = self._get_x_y(other)
        return Point(self.x + x, self.y + y)

    def __sub__(self, other):
        x, y = self._get_x_y(other)
        return Point(self.x - x, self.y - y)

    def __mul__(self, other):
        x, y = self._get_x_y(other)
        return Point(self.x * x, self.y * y)

    def __truediv__(self, other):
        x, y = self._get_x_y(other)
        return Point(self.x / x, self.y / y)

    def __round__(self, n=None):
        return Point(round(self.x, n), round(self.y, n))

    def __getitem__(self, index):
        return (self.x, self.y)[index]

    def __iter__(self):
        return iter([self.x, self.y])

    def __str__(self):
        return f"({self.x}, {self.y})"


class Vector:
    __slots__ = ("x", "y")

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

    def dot(self, v):
        return self.x * v.x + self.y * v.y

    def __mul__(self, other):
        return Vector(self.x * other, self.y * other)

    def __truediv__(self, other):
        return Vector(self.x / other, self.y / other)

    def __str__(self):
        return f"({self.x}, {self.y})"


class Points:
    __slots__ = ("points",)

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
    __slots__ = ("points", "parent", "radius_offset", "curve_points_cache", "osu_pixel_multiplier")

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

    def _limit_curve(self):
        new_curve = [self.curve_points_cache[0]]
        max_length = self.parent.length
        current_length = 0
        for i in range(len(self.curve_points_cache)-1):
            p1 = self.curve_points_cache[i]
            p2 = self.curve_points_cache[i+1]
            length = p1.distance_to(p2)

            if current_length + length <= max_length:
                new_curve.append(p2)
                if current_length + length == max_length:
                    return np.array(new_curve)
            else:
                return new_curve

            current_length += length

        return new_curve

    def create_curve_functions(self):
        curves = []
        for points in self.points.split():
            curves.append(self._create_curve(points))
        self._save_curve_result(curves)
        self._limit_curve()


class PerfectCircle(CurveBase):
    type = CurveType.PERFECT
    __slots__ = CurveBase.__slots__ + ("radius",)

    def __init__(self, points, parent):
        super().__init__(points, parent)

        self.radius = None

    def _get_t_points(self, min_t, max_t):
        return np.linspace(min_t, max_t, math.ceil(self.parent.length*self.osu_pixel_multiplier))

    def _save_curve_result(self, curve, min_t, max_t):
        t_points = self._get_t_points(min_t, max_t)
        self.curve_points_cache = list(map(lambda p: tuple(curve(p)), t_points))

    @staticmethod
    def get_when_equal_x(p0, p1):
        y = (p0.y + p1.y) / 2
        x = (p0.x ** 2 - p1.x ** 2 + p0.y ** 2 - p1.y ** 2 + 2 * (p1.y - p0.y) * y) / (-2 * (p1.x - p0.x))
        return x, y

    @staticmethod
    def get_when_equal_y(p0, p1):
        x = (p0.x + p1.x) / 2
        y = (p0.x ** 2 - p1.x ** 2 + p0.y ** 2 - p1.y ** 2 + 2 * (p1.x - p0.x) * x) / (-2 * (p1.y - p0.y))
        return x, y

    def create_curve_functions(self):
        p0, p1, p2 = self.points

        if p0.x == p1.x:
            x, y = self.get_when_equal_x(p1, p2)
        elif p1.x == p2.x:
            x, y = self.get_when_equal_x(p0, p1)
        elif p0.y == p1.y:
            x, y = self.get_when_equal_y(p1, p2)
        elif p1.y == p2.y:
            x, y = self.get_when_equal_x(p0, p1)
        else:
            y = (p1.x ** 2 + p1.y ** 2 - p0.x ** 2 - p0.y ** 2) / \
                (2 * (-(p2.y - p1.y) * (p1.x - p0.x) / (p2.x - p1.x) + p1.y - p0.y)) - \
                (p1.x - p0.x) * (p2.x ** 2 + p2.y ** 2 - p1.x ** 2 - p1.y ** 2) / \
                (2 * (p2.x - p1.x) * (-(p2.y - p1.y) * (p1.x - p0.x) / (p2.x - p1.x) + p1.y - p0.y))
            x = (p2.x ** 2 + p2.y ** 2 - p1.x ** 2 - p1.y ** 2) / \
                (2 * (p2.x - p1.x)) - \
                (p2.y - p1.y) * y / (p2.x - p1.x)
        m_point = Point(x, y)
        self.radius = math.sqrt((m_point.x-p0.x)**2 + (m_point.y - p0.y)**2)
        format_angle = lambda a: 2*math.pi - abs(a) if a < 0 else a
        offset_angle = math.atan2(p0.y - m_point.y, p0.x - m_point.x)
        start_angle = format_angle(offset_angle)
        mid_angle = format_angle(format_angle(math.atan2(p1.y-m_point.y, p1.x-m_point.x))-start_angle)
        end_angle = format_angle(format_angle(math.atan2(p2.y-m_point.y, p2.x-m_point.x))-start_angle)

        self._save_curve_result(lambda t: (
            self.radius * math.cos((t if end_angle > mid_angle else 1-t) * 2*math.pi + offset_angle) + m_point.x,
            self.radius * math.sin((t if end_angle > mid_angle else 1-t) * 2*math.pi + offset_angle) + m_point.y
        ), 0, (end_angle if end_angle > mid_angle else 2*math.pi - end_angle)/(2*math.pi))


class Linear(CurveBase):
    type = CurveType.LINEAR

    def _get_t_points(self, lines):
        return [np.linspace(0, 1, math.ceil(line[0].distance_to(line[1])*self.osu_pixel_multiplier)) for line in lines]

    def _save_curve_result(self, line_func, lines, max_t=1):
        t_points = self._get_t_points(lines)
        self.curve_points_cache = sum([
            list(map(
                lambda t: tuple(line_func(t, lines[i])),
                t_points[i]
            ))
            for i in range(len(t_points))],
            []
        )

    def _limit_lines(self, lines):
        limited_lines = []
        max_length = self.parent.length
        current_length = 0
        for line in lines:
            line_length = line[0].distance_to(line[1])

            if current_length + line_length <= max_length:
                limited_lines.append(line)
                if current_length + line_length == max_length:
                    return limited_lines
            else:
                length_left = max_length - current_length
                line_angle = (line[1] - line[0]).v().normalize()
                new_line = (line[0], line[0] + line_angle * length_left)
                limited_lines.append(new_line)
                return limited_lines

            current_length += line_length

        return limited_lines

    def create_curve_functions(self):
        # TODO: limit curve to max length
        # format = lambda lines: list(map(lambda t: (str(t[0]), str(t[1])), lines))
        lines = [(self.points[i], self.points[i + 1]) for i in range(len(self.points) - 1)]
        # print(f"{format(lines)} -> ", end="")
        lines = self._limit_lines(lines)
        # print(format(lines))
        self._save_curve_result((lambda t, line: line[0]*(1-t) + line[1]*t), lines)


class CatMull(CurveBase):
    type = CurveType.CATMULL

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
            return (0.5 *
                    (2 * p1.x +
                     (-p0.x + p2.x) * t +
                     (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 +
                     (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3),
                    ), (0.5 *
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
        if type == "P":
            if len(points) == 2:
                type = "B"
            else:
                p0, p1, p2 = points
                if p0.slope(p1) == p1.slope(p2):
                    type = "B"
        return {
            "B": Bezier,
            "P": PerfectCircle,
            "L": Linear,
            "C": CatMull,
        }[type](points, parent)
