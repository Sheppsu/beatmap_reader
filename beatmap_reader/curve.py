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
            if i+offset+1 >= len(points):
                break
            if points[i+offset] == points[i+offset+1]:
                points[i+offset].anchor_point = True
                offset += 1
                points.pop(i+offset)
        self.points = points

    def split(self):
        points = [[]]
        for point in self.points:
            points[-1].append(point)
            if point.anchor_point:
                points.append([point])
        return points

    def __iter__(self):
        return iter(self.points)

    def __getitem__(self, index):
        return self.points[index]

    def __len__(self):
        return len(self.points)

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
        self.radius_offset = (54.4 - 4.48 * self.parent.parent.difficulty.circle_size) / 2
        self.curve_points_cache = None

    def create_curve_functions(self):
        raise NotImplementedError()

    def _get_t_points(self, max_t=1):
        return np.linspace(0, max_t, math.ceil(self.parent.length)), np.linspace(0, max_t, math.ceil(self.parent.length))

    def _save_curve_result(self, offset_curves, max_t=1):
        raise NotImplementedError()

    @property
    def curve_points(self):
        if self.curve_points_cache is None:
            self.create_curve_functions()
        return self.curve_points_cache


class Bezier(CurveBase):
    type = CurveType.BEZIER

    def __init__(self, points, parent):
        super().__init__(points, parent)


class PerfectCircle(CurveBase):
    type = CurveType.PERFECT

    def __init__(self, points, parent):
        super().__init__(points, parent)

        self.radius1 = None
        self.radius2 = None

    def _get_t_points(self, max_t=1):
        return np.linspace(0, max_t, math.ceil(self.radius1*2*math.pi*(max_t/1))), \
               np.linspace(0, max_t, math.ceil(self.radius2*2*math.pi*(max_t/1)))

    def _save_curve_result(self, offset_curves, max_t=1):
        t_points = self._get_t_points(max_t)
        self.curve_points_cache = (
            list(map(lambda p: tuple(map(round, offset_curves[0](p))), t_points[0])),
            list(map(lambda p: tuple(map(round, offset_curves[1](p))), t_points[1]))
        )

    def create_curve_functions(self):
        p0, p1, p2 = self.points
        y = (p1.x**2 + p1.y**2 - p0.x**2 - p0.y**2) / \
            (2*(-(p2.y - p1.y)*(p1.x - p0.x)/(p2.x-p1.x) + p1.y - p0.y)) - \
            (p1.x - p0.x)*(p2.x**2 + p2.y**2 - p1.x**2 - p1.y**2) / \
            (2*(p2.x-p1.x)*(-(p2.y-p1.y)*(p1.x-p0.x)/(p2.x-p1.x)+p1.y-p0.y))
        x = (p2.x**2 + p2.y**2 - p1.x**2 - p1.y**2) / \
            (2*(p2.x-p1.x)) - \
            (p2.y - p1.y)*y / (p2.x - p1.x)
        m_point = Point(x, y)
        radius = math.sqrt((m_point.x-p0.x)**2 + (m_point.y - p0.y)**2)
        self.radius1, self.radius2 = radius - self.radius_offset, radius + self.radius_offset
        start_angle = 2*math.pi-math.atan2(p0.y-m_point.y, p0.x-m_point.x)
        circle = (
            lambda r: (
                lambda t: (
                    (r*math.cos((1-t)*start_angle) + m_point.x),
                    (r*math.sin((1-t)*start_angle) + m_point.y)
                )
            )
        )
        self._save_curve_result((circle(self.radius1), circle(self.radius2)), self.parent.length / (2*math.pi*radius))


class Linear(CurveBase):
    type = CurveType.LINEAR

    def __init__(self, points, parent):
        super().__init__(points, parent)

    @staticmethod
    def get_offset_point(p0, p1, p2, p0o):
        m0 = p0.slope(p1)
        m2 = p2.slope(p1)
        m1 = math.tan(
            ((math.atan(m0) if m0 is not None else -math.pi) +
             (math.atan(m2) if m2 is not None else -math.pi)) /
            2 + math.pi)
        pox = (m1 * p1.x - m0 * p0o.x + p0o.y - p1.y) / (m1 - m0) if m0 is not None else p0o.x
        poy = m1 * (pox - p1.x) + p1.y
        return Point(pox, poy)

    def _save_curve_result(self, offset_curves, max_t=1):
        self.curve_points_cache = [list(map(lambda p: tuple(round(p)), oc)) for oc in offset_curves]

    def create_curve_functions(self):
        # TODO: incorporate max t
        offset_points = ([], [])
        total_length = 0
        for i in range(len(self.points)-1):
            total_length += self.points[i].distance_to(self.points[i+1])
            if i == 0:
                p0, p1 = self.points[i], self.points[i + 1]
                offset_vector = p0.perpendicular_vector(p1)*self.radius_offset
                offset_points[0].append(p0 + offset_vector)
                offset_points[1].append(p0 - offset_vector)
            elif i == len(self.points)-2:
                p0, p1 = self.points[i], self.points[i + 1]
                offset_vector = p0.perpendicular_vector(p1) * self.radius_offset
                offset_points[0].append(p1 + offset_vector)
                offset_points[1].append(p1 - offset_vector)
            else:
                offset_points[0].append(self.get_offset_point(*self.points[i-1:i+2], offset_points[0][i-1]))
                offset_points[1].append(self.get_offset_point(*self.points[i-1:i+2], offset_points[1][i-1]))

        self._save_curve_result(offset_points)


class CatMull(CurveBase):
    type = CurveType.CATMULL

    def __init__(self, points, parent):
        super().__init__(points, parent)


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
